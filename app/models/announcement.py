from datetime import datetime
from app import db

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    classroom = db.relationship('Classroom', back_populates='announcements')
    teacher = db.relationship('User', back_populates='announcements')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'teacher_name': self.teacher.username if self.teacher else None,
            'classroom_id': self.classroom_id
        }
        
    def __repr__(self):
        return f'<Announcement {self.id} for Classroom {self.classroom_id}>'
