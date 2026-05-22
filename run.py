from app import create_app, db
from app.models import seed_demo_data


app = create_app()

with app.app_context():
    db.create_all()
    seed_demo_data()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
