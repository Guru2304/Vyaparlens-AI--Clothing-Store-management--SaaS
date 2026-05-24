from datetime import datetime
from functools import wraps

from flask import flash, redirect, session, url_for

from .models import Merchant


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("merchant_id"):
            flash("Please login to continue.", "error")
            return redirect(url_for("auth.auth"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    merchant_id = session.get("merchant_id")
    if not merchant_id:
        return None
    return Merchant.query.get(merchant_id)


def get_current_owner_id():
    return session.get("merchant_id")


def current_merchant():
    owner_id = get_current_owner_id()
    if not owner_id:
        return None
    return Merchant.query.get(owner_id)


def is_owner():
    return session.get("role", "owner") == "owner"


def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("merchant_id"):
            flash("Please login to continue.", "error")
            return redirect(url_for("auth.auth"))
        if not is_owner():
            flash("You do not have permission to view this page.", "error")
            return redirect(url_for("billing.billing"))
        return view(*args, **kwargs)

    return wrapped


def billing_allowed(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("merchant_id"):
            flash("Please login to continue.", "error")
            return redirect(url_for("auth.auth"))
        if not is_owner():
            flash("You do not have permission to view this page.", "error")
            return redirect(url_for("auth.auth"))
        return view(*args, **kwargs)

    return wrapped


def format_currency(value):
    try:
        value = float(value or 0)
        return f"₹{value:,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def money(value):
    return format_currency(value)


def display_product_name(brand_name, product_name):
    brand = (brand_name or "").strip()
    name = (product_name or "").strip()

    if not brand:
        return name
    if not name:
        return brand
    if name.lower().startswith(brand.lower()):
        return name
    return f"{brand} {name}"


def generate_invoice_number(merchant_id):
    from .models import Bill

    today = datetime.now()
    date_part = today.strftime("%y%m%d")
    prefix = f"INV-{date_part}"
    count_today = Bill.query.filter(
        Bill.merchant_id == merchant_id,
        Bill.bill_number.like(f"{prefix}-%"),
    ).count()
    return f"{prefix}-{count_today + 1:04d}"


def calculate_item_pricing(default_unit_price, quantity, discount_type="none", discount_value=0, custom_final_price=None):
    try:
        default_unit_price = float(default_unit_price or 0)
        quantity = int(quantity or 0)
        discount_value = float(discount_value or 0)
    except (TypeError, ValueError):
        return {"error": "Invalid item price or quantity."}

    discount_type = (discount_type or "none").strip().lower()

    if discount_type == "percentage":
        discount_type = "percent"

    final_unit_price = default_unit_price
    error = None

    if quantity <= 0:
        error = "Quantity must be positive."
    elif discount_type in ["none", ""]:
        final_unit_price = default_unit_price
    elif discount_type == "flat":
        if discount_value < 0:
            error = "Flat discount cannot be negative."
        elif discount_value > default_unit_price:
            error = "Flat discount cannot exceed default price."
        final_unit_price = default_unit_price - discount_value
    elif discount_type == "percent":
        if discount_value < 0:
            error = "Percentage discount cannot be negative."
        elif discount_value > 100:
            error = "Percentage discount cannot exceed 100."
        final_unit_price = default_unit_price - (default_unit_price * discount_value / 100)
    elif discount_type == "custom_price":
        try:
            final_unit_price = float(custom_final_price if custom_final_price not in [None, ""] else default_unit_price)
        except (TypeError, ValueError):
            error = "Custom final price must be a valid number."
            final_unit_price = default_unit_price
        if final_unit_price < 0:
            error = "Custom final price cannot be negative."
    else:
        error = "Invalid item discount type."

    final_unit_price = max(round(final_unit_price, 2), 0)
    line_subtotal = round(default_unit_price * quantity, 2)
    line_total = round(final_unit_price * quantity, 2)
    discount_amount = max(round(line_subtotal - line_total, 2), 0)
    discount_per_unit = max(round(default_unit_price - final_unit_price, 2), 0)

    return {
        "default_unit_price": round(default_unit_price, 2),
        "quantity": quantity,
        "discount_type": discount_type or "none",
        "discount_value": round(discount_value, 2),
        "final_unit_price": final_unit_price,
        "discount_per_unit": discount_per_unit,
        "line_subtotal": line_subtotal,
        "line_total": line_total,
        "discount_amount": discount_amount,
        "error": error,
    }


def parse_tokens(raw_value):
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def today_range():
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
