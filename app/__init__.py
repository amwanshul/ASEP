from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Ensure upload directory exists
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        # Import models
        from app.models.user import User
        from app.models.classroom import Classroom, ClassroomMember, Resource
        from app.models.announcement import Announcement
        from app.models.forum import ForumPost, ForumComment
        from app.models.notification import Notification
        from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
        from app.models.achievement import Achievement, UserAchievement, Leaderboard
        from app.models.file_attachment import FileAttachment
        from app.models.teacher_ping import TeacherPing

        @login_manager.user_loader
        def load_user(id):
            return User.query.get(int(id))

        # Register blueprints
        from app.routes import main, auth, classroom, forum, notifications, quiz
        app.register_blueprint(main.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(classroom.bp)
        app.register_blueprint(forum.bp)
        app.register_blueprint(notifications.bp)
        app.register_blueprint(quiz.bp)

    return app
