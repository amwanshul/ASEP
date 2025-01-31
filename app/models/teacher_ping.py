from datetime import datetime
from app import db

class TeacherPing(db.Model):
    __tablename__ = 'teacher_pings'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='unread')
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], back_populates='pings_sent')
    teacher = db.relationship('User', foreign_keys=[teacher_id], back_populates='pings_received')

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id,
            'student': self.student.username,
            'teacher': self.teacher.username
        }
    
    def __repr__(self):
        return f'<TeacherPing {self.id}>'
