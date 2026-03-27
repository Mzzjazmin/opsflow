from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
    from app import db
from app.models import User

@app.before_first_request
def create_users():
    db.create_all()

    if not User.query.first():
        user1 = User(full_name="Admin User", email="admin@test.com", password="1234", role="admin")
        user2 = User(full_name="John Staff", email="john@test.com", password="1234", role="staff")
        user3 = User(full_name="Mary Supervisor", email="mary@test.com", password="1234", role="supervisor")

        db.session.add_all([user1, user2, user3])
        db.session.commit()