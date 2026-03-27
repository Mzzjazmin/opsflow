from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.routes import main
    from app.auth import auth
    from app.models import User

    app.register_blueprint(main)
    app.register_blueprint(auth)

    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email="admin@test.com").first():
            admin = User(
                full_name="Admin User",
                email="admin@test.com",
                password="1234",
                role="admin"
            )
            john = User(
                full_name="John Staff",
                email="john@test.com",
                password="1234",
                role="staff"
            )
            mary = User(
                full_name="Mary Supervisor",
                email="mary@test.com",
                password="1234",
                role="supervisor"
            )

            db.session.add_all([admin, john, mary])
            db.session.commit()

    return app