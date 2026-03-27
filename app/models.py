from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="staff")


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="New")
    priority = db.Column(db.String(50), default="Medium")

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User", backref="tasks")

    approval_status = db.Column(db.String(50), default="Not Required")


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="Open")

    raised_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    raised_by = db.relationship("User", foreign_keys=[raised_by_id], backref="raised_issues")

    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id], backref="assigned_issues")

    investigation_note = db.Column(db.Text)
    resolution_note = db.Column(db.Text)


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    performed_by = db.relationship("User", backref="activity_logs")
    timestamp = db.Column(db.DateTime, server_default=db.func.now())