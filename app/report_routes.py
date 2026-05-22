import json

from flask import Blueprint, render_template
from sqlalchemy import func

from .analytics import (
    calculate_best_selling_variants,
    calculate_highest_margin_products,
    calculate_highest_profit_products,
    calculate_inventory_value,
    calculate_low_stock_items,
    calculate_payment_summary,
    calculate_slow_moving_stock,
    calculate_top_selling_products,
    calculate_udhar_pending,
    category_sales,
    daily_sales_series,
)
from .helpers import current_merchant, display_product_name, login_required
from .models import Bill, BillItem


report_bp = Blueprint("reports", __name__, url_prefix="/reports")


@report_bp.route("/")
@login_required
def reports():
    merchant = current_merchant()
    gross_sales = sum(bill.total_amount for bill in Bill.query.filter_by(merchant_id=merchant.id).all())
    gross_profit = sum(bill.gross_profit for bill in Bill.query.filter_by(merchant_id=merchant.id).all())
    total_bills = Bill.query.filter_by(merchant_id=merchant.id).count()
    average_margin = (gross_profit / gross_sales * 100) if gross_sales else 0
    inventory_value = calculate_inventory_value(merchant.id)
    payment_summary = calculate_payment_summary(merchant.id)
    top_products = calculate_top_selling_products(merchant.id)
    best_variants = calculate_best_selling_variants(merchant.id)
    highest_profit = calculate_highest_profit_products(merchant.id)
    highest_margin = calculate_highest_margin_products(merchant.id)
    low_stock = calculate_low_stock_items(merchant.id)
    slow_stock = calculate_slow_moving_stock(merchant.id)
    pending_udhar = calculate_udhar_pending(merchant.id)
    daily_series = daily_sales_series(merchant.id)
    categories = category_sales(merchant.id)

    top_product_chart = {
        "labels": [display_product_name(row.brand_name, row.product_name) for row in top_products[:8]],
        "values": [row.sold_qty or 0 for row in top_products[:8]],
    }
    payment_chart = {
        "labels": list(payment_summary.keys()),
        "values": [round(value, 2) for value in payment_summary.values()],
    }
    category_chart = {
        "labels": [row["category"] for row in categories],
        "values": [round(row["revenue"], 2) for row in categories],
    }

    return render_template(
        "reports.html",
        merchant=merchant,
        page_title="Reports",
        gross_sales=gross_sales,
        gross_profit=gross_profit,
        average_margin=average_margin,
        total_bills=total_bills,
        pending_udhar=pending_udhar,
        inventory_value=inventory_value,
        top_products=top_products[:8],
        best_variants=best_variants[:8],
        highest_profit=highest_profit[:8],
        highest_margin=highest_margin[:8],
        low_stock=low_stock[:8],
        slow_stock=slow_stock[:8],
        daily_series=json.dumps(daily_series),
        payment_chart=json.dumps(payment_chart),
        top_product_chart=json.dumps(top_product_chart),
        category_chart=json.dumps(category_chart),
    )
