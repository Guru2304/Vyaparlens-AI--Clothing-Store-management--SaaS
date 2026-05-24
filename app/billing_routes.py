import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import db
from .helpers import (
    billing_allowed,
    calculate_item_pricing,
    current_merchant,
    display_product_name,
    generate_invoice_number,
    is_owner,
    safe_float,
    safe_int,
)
from .models import Bill, BillItem, CreditTransaction, Customer, Product, Variant


billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


def _product_payload(merchant_id):
    products = Product.query.filter_by(merchant_id=merchant_id).order_by(Product.product_name.asc()).all()
    payload = []
    for product in products:
        payload.append(
            {
                "id": product.id,
                "brand_name": product.brand_name,
                "product_name": product.product_name,
                "display_name": display_product_name(product.brand_name, product.product_name),
                "category": product.category,
                **({"buying_price": product.buying_price} if is_owner() else {}),
                "selling_price": product.selling_price,
                "minimum_selling_price": product.minimum_selling_price,
                "variants": [
                    {
                        "id": variant.id,
                        "colour": variant.colour,
                        "size": variant.size,
                        "quantity": variant.quantity,
                        "sku": variant.sku,
                    }
                    for variant in product.variants
                ],
            }
        )
    return payload


@billing_bp.route("/", methods=["GET"], strict_slashes=False)
@billing_allowed
def billing():
    merchant = current_merchant()
    customers = Customer.query.filter_by(merchant_id=merchant.id).order_by(Customer.name.asc()).all()
    return render_template(
        "billing.html",
        merchant=merchant,
        page_title="Billing",
        products_json=json.dumps(_product_payload(merchant.id)),
        customers=customers,
    )


def _get_customer(merchant, pending_amount):
    existing_customer_id = safe_int(request.form.get("customer_id"))
    customer = None
    if existing_customer_id:
        customer = Customer.query.filter_by(id=existing_customer_id, merchant_id=merchant.id).first()
    if not customer and pending_amount > 0:
        name = request.form.get("customer_name", "").strip()
        mobile = request.form.get("customer_mobile", "").strip()
        address = request.form.get("customer_address", "").strip()
        if not name or not mobile:
            return None, "Customer name and mobile are required for udhar."
        customer = Customer.query.filter_by(merchant_id=merchant.id, mobile=mobile).first()
        if customer:
            customer.name = name or customer.name
            customer.address = address or customer.address
        else:
            customer = Customer(
                merchant_id=merchant.id,
                name=name,
                mobile=mobile,
                address=address,
            )
            db.session.add(customer)
            db.session.flush()
    return customer, None


def _prepare_bill_items(merchant_id, cart):
    subtotal = 0
    discount_total = 0
    total_amount = 0
    gross_profit = 0
    prepared = []

    for item in cart:
        variant_id = safe_int(item.get("variantId", item.get("variant_id")))
        quantity = safe_int(item.get("quantity"))
        discount_type = item.get("discountType", item.get("discount_type", "none"))
        discount_value = safe_float(item.get("discountValue", item.get("discount_value")))
        custom_final_price = item.get("customFinalPrice", item.get("custom_final_price"))

        variant = Variant.query.join(Product).filter(
            Variant.id == variant_id,
            Variant.merchant_id == merchant_id,
            Product.merchant_id == merchant_id,
        ).first()

        if not variant:
            return None, 0, 0, 0, 0, "A selected variant no longer exists."
        if quantity <= 0:
            return None, 0, 0, 0, 0, "Quantity must be positive."
        if quantity > variant.quantity:
            product_label = display_product_name(variant.product.brand_name, variant.product.product_name)
            return None, 0, 0, 0, 0, f"Only {variant.quantity} pieces available for {product_label} {variant.colour}-{variant.size}."

        product = variant.product
        legacy_selling_price = item.get("sellingPrice", item.get("price"))
        if discount_type in [None, "", "none"] and legacy_selling_price not in [None, ""]:
            legacy_price = safe_float(legacy_selling_price)
            if round(legacy_price, 2) != round(product.selling_price or 0, 2):
                discount_type = "custom_price"
                custom_final_price = legacy_price

        pricing = calculate_item_pricing(
            product.selling_price,
            quantity,
            discount_type=discount_type,
            discount_value=discount_value,
            custom_final_price=custom_final_price,
        )
        if pricing.get("error"):
            return None, 0, 0, 0, 0, pricing["error"]

        cost = round(product.buying_price * quantity, 2)
        profit = round(pricing["line_total"] - cost, 2)
        subtotal += pricing["line_subtotal"]
        discount_total += pricing["discount_amount"]
        total_amount += pricing["line_total"]
        gross_profit += profit
        prepared.append(
            {
                "variant": variant,
                "product": product,
                "quantity": quantity,
                "selling_price": pricing["final_unit_price"],
                "default_unit_price": pricing["default_unit_price"],
                "discount": pricing["discount_amount"],
                "line_subtotal": pricing["line_subtotal"],
                "line_total": pricing["line_total"],
                "profit": profit,
            }
        )

    return prepared, round(subtotal, 2), round(discount_total, 2), round(total_amount, 2), round(gross_profit, 2), None


def _apply_settlement_discount(prepared_items, settlement_discount):
    """Apply an accepted lower collection amount across items as extra discount."""
    settlement_discount = round(float(settlement_discount or 0), 2)
    if settlement_discount <= 0:
        return round(sum(item["profit"] for item in prepared_items), 2)

    base_total = round(sum(item["line_total"] for item in prepared_items), 2)
    if base_total <= 0:
        return round(sum(item["profit"] for item in prepared_items), 2)

    remaining_discount = settlement_discount
    gross_profit = 0
    for index, item in enumerate(prepared_items):
        if index == len(prepared_items) - 1:
            share = remaining_discount
        else:
            share = round((item["line_total"] / base_total) * settlement_discount, 2)
            remaining_discount = round(remaining_discount - share, 2)

        share = min(max(share, 0), item["line_total"])
        item["discount"] = round(item["discount"] + share, 2)
        item["line_total"] = round(item["line_total"] - share, 2)
        item["selling_price"] = round(item["line_total"] / item["quantity"], 2) if item["quantity"] else 0
        cost = round(item["product"].buying_price * item["quantity"], 2)
        item["profit"] = round(item["line_total"] - cost, 2)
        gross_profit += item["profit"]

    return round(gross_profit, 2)


@billing_bp.route("/create", methods=["POST"])
@billing_allowed
def create_bill():
    merchant = current_merchant()
    try:
        cart = json.loads(request.form.get("cart_data") or "[]")
    except json.JSONDecodeError:
        cart = []
    if not isinstance(cart, list) or not cart:
        flash("Add at least one item to the bill.", "error")
        return redirect(url_for("billing.billing"))

    payment_mode = request.form.get("payment_mode", "Cash")
    paid_amount = round(safe_float(request.form.get("paid_amount")), 2)
    mixed_cash = round(safe_float(request.form.get("mixed_cash_amount")), 2)
    mixed_upi = round(safe_float(request.form.get("mixed_upi_amount")), 2)
    mixed_card = round(safe_float(request.form.get("mixed_card_amount")), 2)

    prepared_items, subtotal, discount_amount, total_amount, gross_profit, cart_error = _prepare_bill_items(merchant.id, cart)
    if cart_error:
        flash(cart_error, "error")
        return redirect(url_for("billing.billing"))
    if total_amount < 0:
        flash("Total amount cannot be less than zero.", "error")
        return redirect(url_for("billing.billing"))

    settlement_modes = ["Cash", "UPI", "Card"]
    if payment_mode == "Udhar":
        paid_amount = 0
    elif paid_amount <= 0 and payment_mode in settlement_modes:
        paid_amount = total_amount
    elif payment_mode in settlement_modes and paid_amount < total_amount:
        accepted_discount = round(total_amount - paid_amount, 2)
        gross_profit = _apply_settlement_discount(prepared_items, accepted_discount)
        discount_amount = round(discount_amount + accepted_discount, 2)
        total_amount = round(paid_amount, 2)

    if paid_amount > total_amount:
        flash("Paid amount cannot exceed total amount.", "error")
        return redirect(url_for("billing.billing"))

    if payment_mode == "Mixed":
        mixed_total = round(mixed_cash + mixed_upi + mixed_card, 2)
        if round(paid_amount, 2) != mixed_total:
            flash("Mixed payment total must equal paid amount.", "error")
            return redirect(url_for("billing.billing"))
    else:
        mixed_cash = mixed_upi = mixed_card = 0

    pending_amount = round(total_amount - paid_amount, 2)
    if pending_amount > 0 and payment_mode not in ["Udhar", "Partial Payment", "Mixed"]:
        payment_mode = "Partial Payment"

    customer, customer_error = _get_customer(merchant, pending_amount)
    if customer_error:
        flash(customer_error, "error")
        return redirect(url_for("billing.billing"))
    if (payment_mode == "Udhar" or pending_amount > 0) and not customer:
        flash("Customer is required for udhar or partial payment.", "error")
        return redirect(url_for("billing.billing"))

    try:
        bill = Bill(
            merchant_id=merchant.id,
            bill_number=generate_invoice_number(merchant.id),
            customer_id=customer.id if customer else None,
            subtotal=round(subtotal, 2),
            discount=round(discount_amount, 2),
            total_amount=round(total_amount, 2),
            paid_amount=round(paid_amount, 2),
            pending_amount=pending_amount,
            payment_mode=payment_mode,
            mixed_cash_amount=round(mixed_cash, 2),
            mixed_upi_amount=round(mixed_upi, 2),
            mixed_card_amount=round(mixed_card, 2),
            gross_profit=round(gross_profit, 2),
        )
        db.session.add(bill)
        db.session.flush()

        touched_products = set()
        for item in prepared_items:
            variant = item["variant"]
            product = item["product"]
            variant.quantity -= item["quantity"]
            touched_products.add(product.id)
            db.session.add(
                BillItem(
                    bill_id=bill.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    product_name=product.product_name,
                    brand_name=product.brand_name,
                    colour=variant.colour,
                    size=variant.size,
                    quantity=item["quantity"],
                    buying_price_at_sale=product.buying_price,
                    selling_price_at_sale=item["selling_price"],
                    discount=round(item["discount"], 2),
                    line_total=round(item["line_total"], 2),
                    profit=round(item["profit"], 2),
                )
            )

        for product_id in touched_products:
            product = Product.query.filter_by(id=product_id, merchant_id=merchant.id).first()
            product.total_quantity = sum(variant.quantity for variant in product.variants)

        if customer and pending_amount > 0:
            customer.total_udhar += round(total_amount, 2)
            customer.paid_amount += round(paid_amount, 2)
            customer.pending_amount += pending_amount
            db.session.add(
                CreditTransaction(
                    merchant_id=merchant.id,
                    customer_id=customer.id,
                    bill_id=bill.id,
                    type="CREDIT_ADDED",
                    amount=round(total_amount, 2),
                    paid_amount=round(paid_amount, 2),
                    pending_amount=pending_amount,
                    payment_mode=payment_mode,
                    note=f"Bill {bill.bill_number}",
                )
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Could not create bill. Please try again.", "error")
        return redirect(url_for("billing.billing"))

    flash("Bill created successfully.", "success")
    return redirect(url_for("billing.receipt", bill_id=bill.id))


@billing_bp.route("/receipt/<int:bill_id>")
@billing_allowed
def receipt(bill_id):
    merchant = current_merchant()
    bill = Bill.query.filter_by(id=bill_id, merchant_id=merchant.id).first_or_404()
    return render_template("receipt.html", merchant=merchant, bill=bill, page_title="Receipt")
