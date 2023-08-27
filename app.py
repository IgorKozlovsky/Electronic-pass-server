from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
from flask import Flask
from database.db import db
from flask_cors import CORS
from dotenv import load_dotenv
from utils.errors import BadRequestException
from utils.http import bad_request, not_found, not_allowed, internal_error
from flask import request, jsonify, send_file, current_app
from models.models import Student, QRCode
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager, logout_user, login_required
import jwt
from datetime import datetime, timedelta
import base64
import qrcode
import uuid

login_manager = LoginManager()

load_dotenv()


def remove_expired_qrcodes():
    with app.app_context():
        expiration_time = datetime.utcnow() - timedelta(seconds=30)
        expired_qrs = QRCode.query.filter(
            QRCode.created_at < expiration_time).all()

        for qr in expired_qrs:
            file_path = f"assets/qrcodes/{qr.uuid}.png"

            if os.path.exists(file_path):
                os.remove(file_path)
                db.session.delete(qr)

        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.getenv("APP_SETTINGS"))
    app.url_map.strict_slashes = False
    db.init_app(app)
    CORS(app)
    Migrate(app, db)
    app.bcrypt = Bcrypt(app)
    login_manager.init_app(app)

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=remove_expired_qrcodes,
                      trigger="interval", seconds=20)
    scheduler.start()

    @login_manager.user_loader
    def load_user(student_id):
        return Student.query.get(int(student_id))

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        remember = data.get("remember", False)

        student = Student.query.filter_by(login=data.get("login")).first()

        if student and student.check_password(data.get("password")):
            with open(f"assets/images/{student.photo}", "rb") as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')

            student_data = student.as_dict()
            student_data["image_data"] = image_data

            if remember:
                token = jwt.encode({
                    'student_id': student.id,
                    'exp': datetime.utcnow() + timedelta(days=3)
                }, app.config['SECRET_KEY'])
                student_data["token"] = token

            return jsonify(student_data), 200

        else:
            raise BadRequestException("Invalid credentials")

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        logout_user()
        return jsonify({"message": "Logged out successfully"}), 200

    @app.route('/create_students', methods=['POST'])
    def create_students():
        students_data = request.get_json()
        for student_data in students_data:
            new_student = Student(
                fullname=student_data["fullname"],
                room=student_data["room"],
                faculty=student_data["faculty"],
                login=student_data["login"],
                photo=student_data["photo"]
            )
            new_student.set_password(student_data["password"])
            db.session.add(new_student)
        db.session.commit()

        return jsonify({"message": "Students created successfully"}), 201

    @app.route('/student/<student_id>', methods=['GET'])
    def get_student_by_id(student_id):
        print(student_id)

        student = Student.query.get(student_id)
        if not student:
            return jsonify({"message": "Student not found"}), 404

        with open(f"assets/images/{student.photo}", "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')

        student_data = student.as_dict()
        student_data["image_data"] = image_data

        return jsonify(student_data), 200

    @app.route('/generate_qr', methods=['POST'])
    def generate_qr():
        student_id = request.json['student_id']

        existing_qr = QRCode.query.filter_by(student_id=student_id).first()

        if existing_qr:
            os.remove(f"assets/qrcodes/{existing_qr.uuid}.png")
            db.session.delete(existing_qr)
            db.session.commit()

        unique_id = str(uuid.uuid4())
        img = qrcode.make(unique_id)

        img_path = f"assets/qrcodes/{unique_id}.png"
        img.save(img_path)

        new_qr = QRCode(
            uuid=unique_id, student_id=request.json['student_id'], created_at=datetime.utcnow())
        db.session.add(new_qr)
        db.session.commit()

        return send_file(img_path, mimetype='image/png'), 200

    @app.route('/scan_qr/<uuid>', methods=['POST'])
    def scan_qr(uuid):
        qr_entry = QRCode.query.filter_by(uuid=uuid).first()
        if not qr_entry or qr_entry.status != "pending":
            return jsonify({"message": "Invalid or already scanned QR code."}), 400

        student = Student.query.get(qr_entry.student_id)
        if not student:
            return jsonify({"message": "Student not found"}), 404

        qr_entry.status = "scanned"
        qr_entry.scanned_at = datetime.utcnow()
        db.session.delete(qr_entry)
        db.session.commit()

        os.remove(f"assets/qrcodes/{uuid}.png")
        q = current_app.config['queue']
        q.put(qr_entry.student_id)

        return jsonify({"message": "QR code scanned and deleted successfully"})

    @app.route('/check_qr_status/<uuid>', methods=['GET'])
    def check_qr_status(uuid):
        qr_entry = QRCode.query.filter_by(uuid=uuid).first()
        if not qr_entry:
            return jsonify({"message": "Invalid QR code."}), 400

        return jsonify({"status": qr_entry.status}), 200

    @app.errorhandler(BadRequestException)
    def bad_request_exception(e):
        return bad_request(e)

    @app.errorhandler(404)
    def route_not_found(e):
        return not_found("route")

    @app.errorhandler(405)
    def method_not_allowed(e):
        return not_allowed(e)

    @app.errorhandler(Exception)
    def internal_server_error(e):
        return internal_error(e)

    return app


app = create_app()
