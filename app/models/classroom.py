from datetime import datetime
from app import db
import random
import string

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(64))
    code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    members = db.relationship('ClassroomMember', back_populates='classroom', lazy='dynamic', cascade='all, delete-orphan')
    teacher = db.relationship('User', back_populates='classrooms_owned', foreign_keys=[teacher_id])
    join_requests = db.relationship('ClassroomRequest', back_populates='classroom', lazy='dynamic', cascade='all, delete-orphan')
    resources = db.relationship('Resource', back_populates='classroom', lazy='dynamic', cascade='all, delete-orphan')
    announcements = db.relationship('Announcement', back_populates='classroom', lazy='dynamic', cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', back_populates='classroom', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def generate_class_code(length=6):
        """Generate a random class code."""
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=length))
            # Check if code already exists
            if not Classroom.query.filter_by(code=code).first():
                return code

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subject': self.subject,
            'code': self.code,
            'teacher_id': self.teacher_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Classroom {self.name}>'

class ClassroomMember(db.Model):
    __tablename__ = 'classroom_members'
    
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), default='student')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    classroom = db.relationship('Classroom', back_populates='members')
    user = db.relationship('User', back_populates='memberships')
    
    def to_dict(self):
        return {
            'id': self.id,
            'classroom_id': self.classroom_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<ClassroomMember {self.user_id} in {self.classroom_id}>'

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    classroom = db.relationship('Classroom', back_populates='resources')
    creator = db.relationship('User', back_populates='resources')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'classroom_id': self.classroom_id,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Resource {self.title}>'
