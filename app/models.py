from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    app_email = db.Column(db.String(150), nullable=True)
    app_password = db.Column(db.String(150), nullable=True)
    emails = db.relationship('EmailLog', backref='user', lazy=True)

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=True) # Could be blank if checking from index
    body = db.Column(db.Text, nullable=False)
    prediction = db.Column(db.String(50), nullable=False) # 'Spam' or 'Ham'
    probability = db.Column(db.Float, nullable=False) # 92.0
    reasons = db.Column(db.Text, nullable=True) # JSON or Comma separated string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
