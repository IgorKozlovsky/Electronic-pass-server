from database.db import db
from flask import current_app
from flask_login import UserMixin
from datetime import datetime


class Student(db.Model, UserMixin):
    def as_dict(self):
        return {
            "id": self.id,
            "fullname": self.fullname,
            "room": self.room,
            "faculty": self.faculty,
            "login": self.login,
            "photo": self.photo
        }

    def set_password(self, password):
        bcrypt = current_app.bcrypt
        self.password_hash = bcrypt.generate_password_hash(
            password).decode('utf-8')

    def check_password(self, password):
        bcrypt = current_app.bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    photo = db.Column(db.String(250), nullable=False)


class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student = db.relationship('Student', backref=db.backref('qr_codes', lazy=True))
    uuid = db.Column(db.String(36), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scanned_at = db.Column(db.DateTime, nullable=True)
