from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile information
    full_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    points = db.Column(db.Integer, default=0)
    
    # Relationships
    classrooms_owned = db.relationship('Classroom', back_populates='teacher', lazy='dynamic', foreign_keys='Classroom.teacher_id')
    memberships = db.relationship('ClassroomMember', back_populates='user', lazy='dynamic')
    classroom_requests = db.relationship('ClassroomRequest', back_populates='user', lazy='dynamic')
    posts = db.relationship('ForumPost', backref='author', lazy='dynamic', foreign_keys='ForumPost.author_id')
    comments = db.relationship('ForumComment', backref='author', lazy='dynamic', foreign_keys='ForumComment.author_id')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')
    announcements = db.relationship('Announcement', back_populates='teacher', lazy='dynamic', foreign_keys='Announcement.teacher_id')
    resources = db.relationship('Resource', back_populates='creator', lazy='dynamic', foreign_keys='Resource.created_by')
    uploaded_files = db.relationship('FileAttachment', back_populates='uploader', lazy='dynamic', foreign_keys='FileAttachment.uploader_id')
    pings_sent = db.relationship('TeacherPing', back_populates='student', lazy='dynamic', foreign_keys='TeacherPing.student_id')
    pings_received = db.relationship('TeacherPing', back_populates='teacher', lazy='dynamic', foreign_keys='TeacherPing.teacher_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
