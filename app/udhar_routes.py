from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from . import db
from .helpers import current_merchant, login_required, safe_float, safe_int
from .models import CreditTransaction, Customer


udhar_bp = Blueprint("udhar", __name__, url_prefix="/udhar")


@udhar_bp.route("/")
@login_required
def udhar():
    merchant = current_merchant()
    customers = Customer.query.filter_by(merchant_id=merchant.id).order_by(Customer.pending_amount.desc()).all()
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    collected_month = db.session.query(func.coalesce(func.sum(CreditTransaction.paid_amount), 0)).filter(
        CreditTransaction.merchant_id == merchant.id,
        CreditTransaction.type == "PAYMENT_RECEIVED",
        CreditTransaction.created_at >= month_start,
    ).scalar()
    pending_total = sum(customer.pending_amount for customer in customers)
    highest_pending = customers[0] if customers else None
    return render_template(
        "udhar.html",
        merchant=merchant,
        page_title="Udhar",
        customers=customers,
        pending_total=pending_total,
        collected_month=collected_month,
        highest_pending=highest_pending,
    )


@udhar_bp.route("/customer/<int:customer_id>")
@login_required
def customer_profile(customer_id):
    merchant = current_merchant()
    customer = Customer.query.filter_by(id=customer_id, merchant_id=merchant.id).first_or_404()
    transactions = CreditTransaction.query.filter_by(
        merchant_id=merchant.id,
        customer_id=customer.id,
    ).order_by(CreditTransaction.created_at.desc()).all()
    return render_template(
        "customer_profile.html",
        merchant=merchant,
        page_title="Customer Profile",
        customer=customer,
        transactions=transactions,
    )


@udhar_bp.route("/collect", methods=["POST"])
@login_required
def collect_payment():
    merchant = current_merchant()
    customer_id = safe_int(request.form.get("customer_id"))
    amount = safe_float(request.form.get("amount"))
    payment_mode = request.form.get("payment_mode", "Cash")
    note = request.form.get("note", "").strip()
    adjustment = request.form.get("adjustment") == "on"

    customer = Customer.query.filter_by(id=customer_id, merchant_id=merchant.id).first()
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("udhar.udhar"))
    if amount <= 0:
        flash("Received amount must be positive.", "error")
        return redirect(url_for("udhar.udhar"))
    if amount > customer.pending_amount and not adjustment:
        flash("Received amount cannot exceed pending amount unless marked as adjustment.", "error")
        return redirect(url_for("udhar.udhar"))

    applied = min(amount, customer.pending_amount)
    customer.paid_amount += applied
    customer.pending_amount = max(customer.pending_amount - applied, 0)
    db.session.add(
        CreditTransaction(
            merchant_id=merchant.id,
            customer_id=customer.id,
            type="PAYMENT_RECEIVED" if not adjustment else "ADJUSTMENT",
            amount=amount,
            paid_amount=applied,
            pending_amount=customer.pending_amount,
            payment_mode=payment_mode,
            note=note,
        )
    )
    db.session.commit()
    flash("Payment collected.", "success")
    return redirect(request.referrer or url_for("udhar.udhar"))
