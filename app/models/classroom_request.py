from app import db
from datetime import datetime

class ClassroomRequest(db.Model):
    __tablename__ = 'classroom_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    message = db.Column(db.Text)  # Optional message from student when requesting to join
    response_message = db.Column(db.Text)  # Optional response message from teacher
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='classroom_requests')
    classroom = db.relationship('Classroom', back_populates='join_requests')

    def __repr__(self):
        return f'<ClassroomRequest {self.id} - User {self.user_id} -> Classroom {self.classroom_id} ({self.status})>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'classroom_id': self.classroom_id,
            'status': self.status,
            'message': self.message,
            'response_message': self.response_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
