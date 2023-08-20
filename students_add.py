import pandas as pd
from models.models import Student
from app import db, create_app

data = pd.read_excel('assets\students.xlsx', engine='openpyxl')

app = create_app()

with app.app_context():
    for index, row in data.iterrows():
        new_student = Student(
            fullname=row["fullname"],
            room=str(row["room"]),
            faculty=row["faculty"],
            login=row["login"],
            photo=row["photo"]
        )
        new_student.set_password(str(row["password"]))

        db.session.add(new_student)

    db.session.commit()
