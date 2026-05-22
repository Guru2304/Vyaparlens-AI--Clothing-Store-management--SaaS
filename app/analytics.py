from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func

from . import db
from .helpers import display_product_name, format_currency, today_range
from .models import Bill, BillItem, Customer, Product, Variant


def calculate_today_sales(merchant_id):
    start, end = today_range()
    return db.session.query(func.coalesce(func.sum(Bill.total_amount), 0)).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= start,
        Bill.created_at <= end,
    ).scalar()


def calculate_today_profit(merchant_id):
    start, end = today_range()
    return db.session.query(func.coalesce(func.sum(Bill.gross_profit), 0)).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= start,
        Bill.created_at <= end,
    ).scalar()


def calculate_today_bills(merchant_id):
    start, end = today_range()
    return Bill.query.filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= start,
        Bill.created_at <= end,
    ).count()


def calculate_payment_summary(merchant_id):
    start, end = today_range()
    bills = Bill.query.filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= start,
        Bill.created_at <= end,
    ).all()
    summary = {"Cash": 0, "UPI": 0, "Card": 0, "Mixed": 0, "Udhar": 0, "Partial Payment": 0}
    for bill in bills:
        if bill.payment_mode == "Mixed":
            summary["Cash"] += bill.mixed_cash_amount or 0
            summary["UPI"] += bill.mixed_upi_amount or 0
            summary["Card"] += bill.mixed_card_amount or 0
            summary["Mixed"] += bill.paid_amount or 0
        else:
            summary[bill.payment_mode] = summary.get(bill.payment_mode, 0) + (bill.paid_amount or 0)
    return summary


def calculate_inventory_value(merchant_id):
    rows = db.session.query(Variant.quantity, Product.buying_price).join(Product).filter(
        Variant.merchant_id == merchant_id,
        Product.merchant_id == merchant_id,
    ).all()
    return sum((quantity or 0) * (buying_price or 0) for quantity, buying_price in rows)


def calculate_low_stock_items(merchant_id):
    return db.session.query(Variant, Product).join(Product).filter(
        Variant.merchant_id == merchant_id,
        Product.merchant_id == merchant_id,
        Variant.quantity <= Product.low_stock_limit,
    ).order_by(Variant.quantity.asc()).all()


def _since(days):
    return datetime.utcnow() - timedelta(days=days)


def calculate_top_selling_products(merchant_id, days=30):
    rows = db.session.query(
        BillItem.product_id,
        BillItem.product_name,
        BillItem.brand_name,
        func.sum(BillItem.quantity).label("sold_qty"),
        func.sum(BillItem.line_total).label("revenue"),
    ).join(Bill).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= _since(days),
    ).group_by(BillItem.product_id, BillItem.product_name, BillItem.brand_name).order_by(
        func.sum(BillItem.quantity).desc()
    ).all()
    return rows


def calculate_best_selling_variants(merchant_id, days=30):
    rows = db.session.query(
        BillItem.product_name,
        BillItem.brand_name,
        BillItem.colour,
        BillItem.size,
        func.sum(BillItem.quantity).label("sold_qty"),
        func.sum(BillItem.line_total).label("revenue"),
    ).join(Bill).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= _since(days),
    ).group_by(
        BillItem.product_name, BillItem.brand_name, BillItem.colour, BillItem.size
    ).order_by(func.sum(BillItem.quantity).desc()).all()
    return rows


def calculate_highest_profit_products(merchant_id, days=30):
    rows = db.session.query(
        BillItem.product_id,
        BillItem.product_name,
        BillItem.brand_name,
        func.sum(BillItem.profit).label("profit"),
    ).join(Bill).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= _since(days),
    ).group_by(BillItem.product_id, BillItem.product_name, BillItem.brand_name).order_by(
        func.sum(BillItem.profit).desc()
    ).all()
    return rows


def calculate_highest_margin_products(merchant_id, days=30):
    rows = db.session.query(
        BillItem.product_id,
        BillItem.product_name,
        BillItem.brand_name,
        func.sum(BillItem.profit).label("profit"),
        func.sum(BillItem.line_total).label("revenue"),
    ).join(Bill).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= _since(days),
    ).group_by(BillItem.product_id, BillItem.product_name, BillItem.brand_name).all()

    margins = []
    for row in rows:
        revenue = row.revenue or 0
        margin = ((row.profit or 0) / revenue * 100) if revenue else 0
        margins.append(
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "brand_name": row.brand_name,
                "profit": row.profit or 0,
                "revenue": revenue,
                "margin": margin,
            }
        )
    return sorted(margins, key=lambda item: item["margin"], reverse=True)


def _sold_by_variant(merchant_id, days):
    rows = db.session.query(
        BillItem.variant_id,
        func.sum(BillItem.quantity).label("sold_qty"),
    ).join(Bill).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= _since(days),
    ).group_by(BillItem.variant_id).all()
    return {row.variant_id: row.sold_qty or 0 for row in rows}


def calculate_slow_moving_stock(merchant_id, days=30):
    sold = _sold_by_variant(merchant_id, days)
    variants = db.session.query(Variant, Product).join(Product).filter(
        Variant.merchant_id == merchant_id,
        Product.merchant_id == merchant_id,
        Variant.quantity > 0,
    ).all()
    return [(variant, product) for variant, product in variants if sold.get(variant.id, 0) == 0]


def calculate_dead_stock(merchant_id, days=60):
    sold = _sold_by_variant(merchant_id, days)
    cutoff = _since(days)
    variants = db.session.query(Variant, Product).join(Product).filter(
        Variant.merchant_id == merchant_id,
        Product.merchant_id == merchant_id,
        Variant.quantity > 0,
        Variant.created_at <= cutoff,
    ).all()
    return [(variant, product) for variant, product in variants if sold.get(variant.id, 0) == 0]


def calculate_udhar_pending(merchant_id):
    return db.session.query(func.coalesce(func.sum(Customer.pending_amount), 0)).filter(
        Customer.merchant_id == merchant_id
    ).scalar()


def generate_restock_suggestions(merchant_id):
    sold = _sold_by_variant(merchant_id, 30)
    suggestions = []
    low_stock_items = calculate_low_stock_items(merchant_id)
    for variant, product in low_stock_items:
        recent_sold = sold.get(variant.id, 0)
        if recent_sold >= max(3, product.low_stock_limit):
            suggestions.append(
                {
                    "message": f"Restock {display_product_name(product.brand_name, product.product_name)} {variant.colour}-{variant.size}. It sold {recent_sold} units in 30 days.",
                    "product": product,
                    "variant": variant,
                }
            )
    return suggestions


def generate_discount_warnings(merchant_id):
    warnings = []
    products = Product.query.filter_by(merchant_id=merchant_id).all()
    for product in products:
        if product.selling_price < product.buying_price:
            warnings.append(f"{display_product_name(product.brand_name, product.product_name)} is priced below buying cost.")
            continue
        revenue = product.selling_price or 0
        margin = ((product.selling_price - product.buying_price) / revenue * 100) if revenue else 0
        if margin < 15:
            warnings.append(f"{display_product_name(product.brand_name, product.product_name)} margin is below 15%.")
        if product.minimum_selling_price and product.minimum_selling_price < product.buying_price:
            warnings.append(f"{display_product_name(product.brand_name, product.product_name)} minimum selling price can create a loss.")
    return warnings


def generate_smart_insights(merchant_id):
    insights = []
    low_stock = calculate_low_stock_items(merchant_id)
    if low_stock:
        variant, product = low_stock[0]
        insights.append(f"{display_product_name(product.brand_name, product.product_name)} {variant.colour}-{variant.size} is low in stock.")

    payment_summary = calculate_payment_summary(merchant_id)
    collections = {key: value for key, value in payment_summary.items() if key != "Mixed" and value > 0}
    if collections:
        best_mode = max(collections, key=collections.get)
        insights.append(f"{best_mode} collection is highest today.")

    pending_customer = Customer.query.filter(
        Customer.merchant_id == merchant_id,
        Customer.pending_amount > 0,
    ).order_by(Customer.pending_amount.desc()).first()
    if pending_customer:
        insights.append(f"{pending_customer.name} has pending udhar of {format_currency(pending_customer.pending_amount)}.")

    slow_stock = calculate_slow_moving_stock(merchant_id, days=30)
    if slow_stock:
        variant, product = slow_stock[0]
        insights.append(f"{variant.colour}-{variant.size} has not sold recently.")

    insights.extend(generate_discount_warnings(merchant_id)[:2])
    if not insights:
        insights.append("Operations look steady. Add more bills to unlock sharper insights.")
    return insights[:6]


def daily_sales_series(merchant_id, days=14):
    start = datetime.utcnow().date() - timedelta(days=days - 1)
    buckets = defaultdict(lambda: {"sales": 0, "profit": 0, "bills": 0})
    bills = Bill.query.filter(Bill.merchant_id == merchant_id, Bill.created_at >= start).all()
    for bill in bills:
        key = bill.created_at.strftime("%d %b")
        buckets[key]["sales"] += bill.total_amount or 0
        buckets[key]["profit"] += bill.gross_profit or 0
        buckets[key]["bills"] += 1

    labels = []
    sales = []
    profit = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        key = day.strftime("%d %b")
        labels.append(key)
        sales.append(round(buckets[key]["sales"], 2))
        profit.append(round(buckets[key]["profit"], 2))
    return {"labels": labels, "sales": sales, "profit": profit}


def category_sales(merchant_id, days=30):
    rows = db.session.query(
        Product.category,
        func.sum(BillItem.line_total).label("revenue"),
    ).join(BillItem, Product.id == BillItem.product_id).join(Bill).filter(
        Bill.merchant_id == merchant_id,
        Bill.created_at >= _since(days),
    ).group_by(Product.category).order_by(func.sum(BillItem.line_total).desc()).all()
    return [{"category": row.category, "revenue": row.revenue or 0} for row in rows]
