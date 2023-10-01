import threading
import queue
from app import app
from window import StudentInfoWindow
from models.models import Student
from flask import current_app


def run_tkinter_app(app, window, q):
    with app.app_context():
        def update_window():
            try:
                student_id = q.get_nowait()
                student = Student.query.get(student_id)
                if student:
                    window.update_info(student)
            except queue.Empty:
                pass
            window.after(100, update_window)

        window.after(100, update_window)
        window.mainloop()


def run_flask_app(app, queue):
    with app.app_context():
        app.config['queue'] = queue
        app.run(debug=False, host='192.168.0.106')


if __name__ == '__main__':
    window = StudentInfoWindow()
    q = queue.Queue()

    flask_thread = threading.Thread(target=run_flask_app, args=(app, q,))
    flask_thread.start()

    run_tkinter_app(app, window, q)
    flask_thread.join()
