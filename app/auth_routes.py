import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import Merchant


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth")
def auth():
    if session.get("merchant_id"):
        return redirect(url_for("main.dashboard"))
    return render_template("auth.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    identifier = request.form.get("identifier", "").strip()
    password = request.form.get("password", "")

    if not identifier or not password:
        flash("Email/mobile and password are required.", "error")
        return redirect(url_for("auth.auth"))

    merchant = Merchant.query.filter(
        (Merchant.email == identifier.lower()) | (Merchant.mobile == identifier)
    ).first()

    if not merchant or not check_password_hash(merchant.password_hash, password):
        flash("Invalid login details.", "error")
        return redirect(url_for("auth.auth"))

    session.clear()
    session.permanent = True
    session["merchant_id"] = merchant.id
    flash("Welcome back.", "success")
    return redirect(url_for("main.dashboard"))


@auth_bp.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name", "").strip()
    shop_name = request.form.get("shop_name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    shop_address = request.form.get("shop_address", "").strip()

    if not all([name, shop_name, mobile, email, password, shop_address]):
        flash("All signup fields are required.", "error")
        return redirect(url_for("auth.auth"))
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        flash("Enter a valid email address.", "error")
        return redirect(url_for("auth.auth"))
    if len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for("auth.auth"))
    if Merchant.query.filter((Merchant.email == email) | (Merchant.mobile == mobile)).first():
        flash("A merchant already exists with this email or mobile.", "error")
        return redirect(url_for("auth.auth"))

    merchant = Merchant(
        name=name,
        shop_name=shop_name,
        mobile=mobile,
        email=email,
        password_hash=generate_password_hash(password),
        shop_address=shop_address,
        receipt_footer="Thank YOU!!!\nVisit Again",
    )
    db.session.add(merchant)
    db.session.commit()

    session.clear()
    session.permanent = True
    session["merchant_id"] = merchant.id
    flash("Account created successfully.", "success")
    return redirect(url_for("main.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.auth"))
