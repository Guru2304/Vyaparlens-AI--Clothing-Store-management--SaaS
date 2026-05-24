from datetime import datetime

from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from . import db


class Merchant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(140), nullable=False, unique=True)
    mobile = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    shop_name = db.Column(db.String(160), nullable=False)
    shop_address = db.Column(db.Text, nullable=False)
    gst_number = db.Column(db.String(30))
    receipt_footer = db.Column(db.String(140), default="Thank YOU!!!\nVisit Again")
    role = db.Column(db.String(20), default="owner", nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("Merchant", remote_side=[id], backref="staff_users")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    brand_name = db.Column(db.String(120), nullable=False)
    product_name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    fabric_type = db.Column(db.String(120))
    gender = db.Column(db.String(40))
    supplier_name = db.Column(db.String(140))
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    mrp = db.Column(db.Float, default=0)
    minimum_selling_price = db.Column(db.Float, default=0)
    low_stock_limit = db.Column(db.Integer, default=5)
    total_quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = db.relationship("Variant", backref="product", cascade="all, delete-orphan", lazy=True)


class Variant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False, index=True)
    colour = db.Column(db.String(60), nullable=False)
    size = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    bill_number = db.Column(db.String(30), nullable=False, unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True)
    subtotal = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    pending_amount = db.Column(db.Float, default=0)
    payment_mode = db.Column(db.String(40), nullable=False)
    mixed_cash_amount = db.Column(db.Float, default=0)
    mixed_upi_amount = db.Column(db.Float, default=0)
    mixed_card_amount = db.Column(db.Float, default=0)
    gross_profit = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("BillItem", backref="bill", cascade="all, delete-orphan", lazy=True)
    customer = db.relationship("Customer", backref="bills")


class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bill.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey("variant.id"), nullable=False)
    product_name = db.Column(db.String(160), nullable=False)
    brand_name = db.Column(db.String(120), nullable=False)
    colour = db.Column(db.String(60), nullable=False)
    size = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    buying_price_at_sale = db.Column(db.Float, nullable=False)
    selling_price_at_sale = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    line_total = db.Column(db.Float, default=0)
    profit = db.Column(db.Float, default=0)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    total_udhar = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    pending_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = db.relationship("CreditTransaction", backref="customer", lazy=True)


class CreditTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False, index=True)
    bill_id = db.Column(db.Integer, db.ForeignKey("bill.id"), nullable=True)
    type = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Float, default=0)
    paid_amount = db.Column(db.Float, default=0)
    pending_amount = db.Column(db.Float, default=0)
    payment_mode = db.Column(db.String(40))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def seed_demo_data():
    ensure_rbac_columns()
    merchant = Merchant.query.filter_by(email="guru@example.com").first()
    if not merchant:
        merchant = Merchant(
            name="Guru Patil",
            shop_name="Guru Fashion",
            mobile="9876543210",
            email="guru@example.com",
            password_hash=generate_password_hash("123456"),
            shop_address="Main Road, Nashik",
            receipt_footer="Thank YOU!!!\nVisit Again",
            role="owner",
            owner_id=None,
            is_active=True,
        )
        db.session.add(merchant)
        db.session.commit()
    else:
        merchant.role = merchant.role or "owner"
        merchant.owner_id = None if merchant.role == "owner" else merchant.owner_id
        merchant.is_active = True if merchant.is_active is None else merchant.is_active
        db.session.commit()

    Merchant.query.filter_by(role="staff").update({"is_active": False})
    db.session.commit()

    existing = Product.query.filter_by(merchant_id=merchant.id, product_name="Bhugoal Shirt").first()
    if existing:
        return

    product = Product(
        merchant_id=merchant.id,
        brand_name="Bhugoal",
        product_name="Bhugoal Shirt",
        category="Shirt",
        fabric_type="Knitted Fabric",
        gender="Men",
        supplier_name="Demo Supplier",
        buying_price=400,
        selling_price=799,
        mrp=999,
        minimum_selling_price=550,
        low_stock_limit=5,
        total_quantity=100,
    )
    db.session.add(product)
    db.session.flush()

    colours = ["Black", "White", "Blue", "Green", "Charcoal", "Maroon", "Yellow", "Red", "Violet", "Gray"]
    size_distribution = {"S": 2, "M": 3, "L": 3, "XL": 1, "XXL": 1}
    for colour in colours:
        for size, qty in size_distribution.items():
            db.session.add(
                Variant(
                    merchant_id=merchant.id,
                    product_id=product.id,
                    colour=colour,
                    size=size,
                    quantity=qty,
                    sku=f"BHUGOAL-SHIRT-{colour[:3].upper()}-{size}",
                )
            )
    db.session.commit()


def ensure_rbac_columns():
    inspector = inspect(db.engine)
    if "merchant" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("merchant")}
    statements = []
    if "role" not in columns:
        statements.append("ALTER TABLE merchant ADD COLUMN role VARCHAR(20) DEFAULT 'owner' NOT NULL")
    if "owner_id" not in columns:
        statements.append("ALTER TABLE merchant ADD COLUMN owner_id INTEGER")
    if "is_active" not in columns:
        statements.append("ALTER TABLE merchant ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL")

    for statement in statements:
        db.session.execute(text(statement))

    if statements:
        db.session.execute(text("UPDATE merchant SET role = 'owner' WHERE role IS NULL OR role = ''"))
        db.session.execute(text("UPDATE merchant SET is_active = 1 WHERE is_active IS NULL"))
        db.session.commit()
