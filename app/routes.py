from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from . import db
from .analytics import (
    calculate_inventory_value,
    calculate_low_stock_items,
    calculate_payment_summary,
    calculate_today_bills,
    calculate_today_profit,
    calculate_today_sales,
    calculate_top_selling_products,
    calculate_udhar_pending,
    generate_smart_insights,
)
from .helpers import current_merchant, display_product_name, login_required, money, safe_float
from .models import Bill, Customer, Product


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_merchant():
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.auth"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    merchant = current_merchant()
    today_sales = calculate_today_sales(merchant.id)
    today_profit = calculate_today_profit(merchant.id)
    today_bills = calculate_today_bills(merchant.id)
    today_udhar = sum(
        bill.pending_amount for bill in Bill.query.filter(
            Bill.merchant_id == merchant.id,
            Bill.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        ).all()
    )
    inventory_value = calculate_inventory_value(merchant.id)
    low_stock = calculate_low_stock_items(merchant.id)
    pending_udhar = calculate_udhar_pending(merchant.id)
    top_products = calculate_top_selling_products(merchant.id)
    payment_summary = calculate_payment_summary(merchant.id)
    recent_bills = Bill.query.filter_by(merchant_id=merchant.id).order_by(Bill.created_at.desc()).limit(8).all()
    insights = generate_smart_insights(merchant.id)
    top_product_name = "No sales yet"
    if top_products:
        top_product_name = display_product_name(top_products[0].brand_name, top_products[0].product_name)

    stats = [
        {"label": "Today Sales", "value": money(today_sales), "hint": "Gross sales today", "tone": "primary"},
        {"label": "Today Profit", "value": money(today_profit), "hint": "Revenue minus product cost", "tone": "success"},
        {"label": "Today Bills", "value": today_bills, "hint": "Invoices created today", "tone": "primary"},
        {"label": "Today Udhar", "value": money(today_udhar), "hint": "Pending from today's bills", "tone": "warning"},
        {"label": "Inventory Value", "value": money(inventory_value), "hint": "Stock cost value", "tone": "primary", "value_class": "currency-value"},
        {"label": "Low Stock Items", "value": len(low_stock), "hint": "Variants at reorder level", "tone": "danger"},
        {"label": "Pending Udhar", "value": money(pending_udhar), "hint": "Total customer credit", "tone": "warning"},
        {"label": "Top Product", "value": top_product_name, "hint": "Best seller in last 30 days", "tone": "success", "value_class": "top-product-name"},
    ]

    return render_template(
        "dashboard.html",
        merchant=merchant,
        page_title="Dashboard",
        stats=stats,
        recent_bills=recent_bills,
        low_stock=low_stock[:8],
        insights=insights,
        payment_summary=payment_summary,
    )


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    merchant = current_merchant()
    if request.method == "POST":
        merchant.name = request.form.get("name", "").strip() or merchant.name
        merchant.shop_name = request.form.get("shop_name", "").strip() or merchant.shop_name
        merchant.mobile = request.form.get("mobile", "").strip() or merchant.mobile
        merchant.email = request.form.get("email", "").strip().lower() or merchant.email
        merchant.shop_address = request.form.get("shop_address", "").strip() or merchant.shop_address
        merchant.gst_number = request.form.get("gst_number", "").strip()
        merchant.receipt_footer = request.form.get("receipt_footer", "").strip() or "Thank YOU!!!\nVisit Again"
        db.session.commit()
        flash("Settings updated.", "success")
        return redirect(url_for("main.settings"))
    return render_template("settings.html", merchant=merchant, page_title="Settings")
