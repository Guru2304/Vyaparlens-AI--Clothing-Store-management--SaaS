from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from . import db
from .helpers import current_merchant, owner_required, safe_int
from .models import Product, Variant


inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("/", strict_slashes=False)
@owner_required
def inventory():
    merchant = current_merchant()
    products = Product.query.filter_by(merchant_id=merchant.id).order_by(Product.product_name.asc()).all()
    categories = sorted({product.category for product in products if product.category})
    brands = sorted({product.brand_name for product in products if product.brand_name})
    return render_template(
        "inventory.html",
        merchant=merchant,
        page_title="Inventory",
        products=products,
        categories=categories,
        brands=brands,
        sensitive_unlocked=bool(session.get("sensitive_unlocked")),
    )


@inventory_bp.route("/stock", methods=["POST"])
@owner_required
def update_stock():
    merchant = current_merchant()
    variant_id = safe_int(request.form.get("variant_id"))
    action = request.form.get("action")
    quantity = safe_int(request.form.get("quantity"))

    variant = Variant.query.join(Product).filter(
        Variant.id == variant_id,
        Variant.merchant_id == merchant.id,
        Product.merchant_id == merchant.id,
    ).first()
    if not variant:
        flash("Variant not found.", "error")
        return redirect(url_for("inventory.inventory"))
    if quantity <= 0:
        flash("Quantity must be positive.", "error")
        return redirect(url_for("inventory.inventory"))

    if action == "reduce":
        if variant.quantity - quantity < 0:
            flash("Stock cannot go below zero.", "error")
            return redirect(url_for("inventory.inventory"))
        variant.quantity -= quantity
    else:
        variant.quantity += quantity

    product = variant.product
    product.total_quantity = sum(item.quantity for item in product.variants)
    db.session.commit()
    flash("Stock updated.", "success")
    return redirect(url_for("inventory.inventory"))
