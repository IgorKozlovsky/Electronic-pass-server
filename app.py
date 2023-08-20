import os
from flask import Flask
from database.db import db
from flask_cors import CORS
from dotenv import load_dotenv
from utils.errors import BadRequestException
from utils.http import bad_request, not_found, not_allowed, internal_error
from flask import request, jsonify
from models.models import Student
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required
import jwt
from datetime import datetime, timedelta

login_manager = LoginManager()

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.getenv("APP_SETTINGS"))
    app.url_map.strict_slashes = False
    db.init_app(app)
    CORS(app)
    Migrate(app, db)
    app.bcrypt = Bcrypt(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(student_id):
        return Student.query.get(int(student_id))

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        remember = data.get("remember", False)

        student = Student.query.filter_by(login=data.get("login")).first()

        if student and student.check_password(data.get("password")):
            login_user(student, remember=remember)

            if remember:
                token = jwt.encode({
                    'student_id': student.id,
                    'exp': datetime.utcnow() + timedelta(days=3)
                }, app.config['SECRET_KEY'])

                return jsonify({"message": "Login successful", "student": student.as_dict(), "token": token}), 200

            return jsonify({"message": "Login successful", "student": student.as_dict()}), 200
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
