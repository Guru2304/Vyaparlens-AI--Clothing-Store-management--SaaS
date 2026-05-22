import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import db
from .helpers import current_merchant, login_required, parse_tokens, safe_float, safe_int
from .models import Product, Variant


product_bp = Blueprint("products", __name__, url_prefix="/products")


DEFAULT_CATEGORIES = [
    "Shirt", "T-Shirt", "Pant", "Jeans", "Track Pant", "Kurti", "Saree",
    "Dress", "Hoodie", "Jacket", "Kids Wear", "Accessories", "Other",
]
DEFAULT_SHIRT_SIZES = ["S", "M", "L", "XL", "XXL"]
DEFAULT_PANT_SIZES = ["28", "30", "32", "34", "36", "38", "40", "42"]
DEFAULT_COLOURS = ["Black", "White", "Blue", "Green", "Charcoal", "Maroon", "Yellow", "Red", "Violet", "Gray"]


@product_bp.route("/", methods=["GET"])
@login_required
def products():
    merchant = current_merchant()
    items = Product.query.filter_by(merchant_id=merchant.id).order_by(Product.created_at.desc()).all()
    return render_template(
        "products.html",
        merchant=merchant,
        page_title="Products",
        products=items,
        categories=DEFAULT_CATEGORIES,
        shirt_sizes=DEFAULT_SHIRT_SIZES,
        pant_sizes=DEFAULT_PANT_SIZES,
        colours=DEFAULT_COLOURS,
        success=request.args.get("success"),
        variant_count=request.args.get("variant_count", 0),
        total_quantity=request.args.get("total_quantity", 0),
        expected_revenue=request.args.get("expected_revenue", 0),
        expected_profit=request.args.get("expected_profit", 0),
    )


def _distribute_equal(total, colours, sizes):
    variants = [(colour, size) for colour in colours for size in sizes]
    base = total // len(variants)
    remainder = total % len(variants)
    quantities = {}
    for index, (colour, size) in enumerate(variants):
        quantities[(colour, size)] = base + (1 if index < remainder else 0)
    return quantities


def _split_colour_totals(total, colour_count):
    base = total // colour_count
    remainder = total % colour_count
    return [base + (1 if index < remainder else 0) for index in range(colour_count)]


def _recommended_for_colour(colour_total, sizes):
    standard = {"S": 0.20, "M": 0.30, "L": 0.30, "XL": 0.15, "XXL": 0.05}
    if set(sizes) == {"S", "M", "L", "XL", "XXL"} and colour_total == 10:
        return {"S": 2, "M": 3, "L": 3, "XL": 1, "XXL": 1}
    weights = {size: standard.get(size, 1) for size in sizes}
    total_weight = sum(weights.values())
    raw = {size: colour_total * weights[size] / total_weight for size in sizes}
    quantities = {size: int(raw[size]) for size in sizes}
    remaining = colour_total - sum(quantities.values())
    ordered = sorted(sizes, key=lambda size: raw[size] - int(raw[size]), reverse=True)
    for size in ordered[:remaining]:
        quantities[size] += 1
    return quantities


def _distribute_recommended(total, colours, sizes):
    colour_totals = _split_colour_totals(total, len(colours))
    quantities = {}
    for colour, colour_total in zip(colours, colour_totals):
        size_quantities = _recommended_for_colour(colour_total, sizes)
        for size in sizes:
            quantities[(colour, size)] = size_quantities.get(size, 0)
    return quantities


def _manual_quantities(raw_json, colours, sizes):
    try:
        rows = json.loads(raw_json or "[]")
    except json.JSONDecodeError:
        return None, "Manual distribution data is invalid."

    if not isinstance(rows, list):
        return None, "Manual distribution data must be a list."

    selected_colours = set(colours)
    selected_sizes = set(sizes)
    quantities = {(colour, size): 0 for colour in colours for size in sizes}
    seen = set()

    for row in rows:
        if not isinstance(row, dict):
            return None, "Manual distribution contains an invalid row."
        colour = str(row.get("colour", "")).strip()
        size = str(row.get("size", "")).strip()
        quantity = safe_int(row.get("quantity"), 0)
        key = (colour, size)

        if colour not in selected_colours or size not in selected_sizes:
            return None, "Manual distribution includes an unselected colour or size."
        if key in seen:
            return None, f"Duplicate quantity found for {colour}-{size}."
        if quantity < 0:
            return None, "Negative quantity is not allowed."

        seen.add(key)
        quantities[key] = quantity

    return quantities, None


@product_bp.route("/add", methods=["POST"])
@login_required
def add_product():
    merchant = current_merchant()
    brand_name = request.form.get("brand_name", "").strip()
    product_name = request.form.get("product_name", "").strip()
    category = request.form.get("category", "").strip()
    custom_category = request.form.get("custom_category", "").strip()
    fabric_type = request.form.get("fabric_type", "").strip()
    gender = request.form.get("gender", "").strip()
    supplier_name = request.form.get("supplier_name", "").strip()
    buying_price = safe_float(request.form.get("buying_price"))
    selling_price = safe_float(request.form.get("selling_price"))
    mrp = safe_float(request.form.get("mrp"))
    minimum_selling_price = safe_float(request.form.get("minimum_selling_price"))
    low_stock_limit = safe_int(request.form.get("low_stock_limit"), 5)
    total_quantity = safe_int(request.form.get("total_quantity"))
    sizes = parse_tokens(request.form.get("sizes"))
    colours = parse_tokens(request.form.get("colours"))
    distribution = request.form.get("distribution_mode") or request.form.get("distribution", "equal")

    if category == "Other" and custom_category:
        category = custom_category

    errors = []
    if not product_name:
        errors.append("Product name is required.")
    if not category:
        errors.append("Category is required.")
    if buying_price <= 0:
        errors.append("Buying price is required.")
    if selling_price <= 0:
        errors.append("Selling price is required.")
    if total_quantity <= 0:
        errors.append("Total quantity is required.")
    if not sizes:
        errors.append("At least one size is required.")
    if not colours:
        errors.append("At least one colour is required.")

    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("products.products"))

    if distribution == "recommended":
        quantities = _distribute_recommended(total_quantity, colours, sizes)
    elif distribution == "manual":
        quantities, manual_error = _manual_quantities(request.form.get("variant_distribution"), colours, sizes)
        if manual_error:
            flash(manual_error, "error")
            return redirect(url_for("products.products"))
    else:
        quantities = _distribute_equal(total_quantity, colours, sizes)

    quantity_sum = sum(quantities.values())
    if quantity_sum < total_quantity:
        flash("Please distribute all quantity before saving.", "error")
        return redirect(url_for("products.products"))
    if quantity_sum > total_quantity:
        flash("Distributed quantity exceeds total quantity.", "error")
        return redirect(url_for("products.products"))

    try:
        product = Product(
            merchant_id=merchant.id,
            brand_name=brand_name or "Generic",
            product_name=product_name,
            category=category,
            fabric_type=fabric_type,
            gender=gender,
            supplier_name=supplier_name,
            buying_price=buying_price,
            selling_price=selling_price,
            mrp=mrp,
            minimum_selling_price=minimum_selling_price,
            low_stock_limit=low_stock_limit,
            total_quantity=total_quantity,
        )
        db.session.add(product)
        db.session.flush()

        for colour in colours:
            for size in sizes:
                sku = f"{brand_name[:4].upper() or 'ITEM'}-{product.id}-{colour[:3].upper()}-{size}".replace(" ", "")
                db.session.add(
                    Variant(
                        merchant_id=merchant.id,
                        product_id=product.id,
                        colour=colour,
                        size=size,
                        quantity=quantities[(colour, size)],
                        sku=sku,
                    )
                )
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Could not save product. Please check the details and try again.", "error")
        return redirect(url_for("products.products"))

    flash("Product added successfully.", "success")
    expected_revenue = selling_price * total_quantity
    expected_profit = (selling_price - buying_price) * total_quantity
    return redirect(
        url_for(
            "products.products",
            success=1,
            variant_count=len(colours) * len(sizes),
            total_quantity=total_quantity,
            expected_revenue=round(expected_revenue, 2),
            expected_profit=round(expected_profit, 2),
        )
    )
