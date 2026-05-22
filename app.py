from app import create_app, db
from app.models import seed_demo_data


flask_app = create_app()

with flask_app.app_context():
    db.create_all()
    seed_demo_data()


app = flask_app


if __name__ == "__main__":
    app.run(debug=True)
