from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Import all models to ensure they are registered with SQLAlchemy
        from app.models.user import User
        from app.models.classroom import Classroom, ClassroomMember, Resource
        from app.models.announcement import Announcement
        from app.models.forum import ForumPost, ForumComment
        from app.models.notification import Notification
        from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
        from app.models.achievement import Achievement, UserAchievement, Leaderboard

        # Create all database tables
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")

    app.run(debug=True)
