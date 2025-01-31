from datetime import datetime
from app import db

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id', ondelete='CASCADE'), nullable=False)
    
    # Post status
    is_resolved = db.Column(db.Boolean, default=False)
    is_escalated = db.Column(db.Boolean, default=False)
    votes = db.Column(db.Integer, default=0)
    
    # Relationships
    comments = db.relationship('ForumComment', back_populates='post', lazy='dynamic', cascade='all, delete-orphan')
    votes_rel = db.relationship('PostVote', back_populates='post', lazy='dynamic', cascade='all, delete-orphan')
    classroom = db.relationship('Classroom', back_populates='forum_posts')
    
    def __repr__(self):
        return f'<ForumPost {self.id}>'

class ForumComment(db.Model):
    __tablename__ = 'forum_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id', ondelete='CASCADE'), nullable=False)
    
    # Comment status
    is_solution = db.Column(db.Boolean, default=False)
    votes = db.Column(db.Integer, default=0)
    
    # Relationships
    post = db.relationship('ForumPost', back_populates='comments')
    
    def __repr__(self):
        return f'<ForumComment {self.id}>'

class PostVote(db.Model):
    __tablename__ = 'post_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id', ondelete='CASCADE'), nullable=False)
    vote_type = db.Column(db.String(10))  # upvote, downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    post = db.relationship('ForumPost', back_populates='votes_rel')
    user = db.relationship('User', backref='post_votes')
    
    def __repr__(self):
        return f'<PostVote {self.id}>'
