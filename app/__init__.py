from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()


def create_app():
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config.from_object(Config)

    instance_dir = Path(__file__).resolve().parent.parent / "instance"
    instance_dir.mkdir(exist_ok=True)

    db.init_app(app)

    from .helpers import display_product_name, format_currency, money

    app.jinja_env.filters["money"] = money
    app.jinja_env.filters["currency"] = format_currency
    app.jinja_env.globals["display_product_name"] = display_product_name

    from .auth_routes import auth_bp
    from .billing_routes import billing_bp
    from .inventory_routes import inventory_bp
    from .product_routes import product_bp
    from .report_routes import report_bp
    from .routes import main_bp
    from .udhar_routes import udhar_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(udhar_bp)
    app.register_blueprint(report_bp)

    return app
