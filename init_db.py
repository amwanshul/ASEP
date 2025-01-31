from app import create_app, db
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember, Resource
from app.models.quiz import Quiz, QuizQuestion, QuizChoice, QuizAttempt, QuizAnswer
import os

def init_db():
    app = create_app()
    with app.app_context():
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join('app', 'static', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        # Create a test teacher account
        teacher = User(
            username='teacher',
            email='teacher@example.com',
            role='teacher'
        )
        teacher.set_password('Teacher123')
        
        # Create a test student account
        student = User(
            username='student',
            email='student@example.com',
            role='student'
        )
        student.set_password('Student123')
        
        try:
            db.session.add(teacher)
            db.session.add(student)
            db.session.commit()
            print("Database initialized successfully!")
            print("\nTest accounts created:")
            print("Teacher - Email: teacher@example.com, Password: Teacher123")
            print("Student - Email: student@example.com, Password: Student123")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    init_db()
