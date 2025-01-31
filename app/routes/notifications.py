from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.announcement import Announcement
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.models.notification import Notification
from app.models.teacher_ping import TeacherPing
from app import db
from datetime import datetime

bp = Blueprint('notifications', __name__)

@bp.route('/classroom/<int:classroom_id>/announcement', methods=['POST'])
@login_required
def create_announcement(classroom_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    classroom = Classroom.query.get_or_404(classroom_id)
    if classroom.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    announcement = Announcement(
        title=data['title'],
        content=data['content'],
        classroom_id=classroom_id,
        teacher_id=current_user.id
    )
    
    db.session.add(announcement)
    db.session.commit()
    
    # Create notifications for all classroom members
    members = ClassroomMember.query.filter_by(classroom_id=classroom_id).all()
    for member in members:
        notification = Notification(
            type='announcement',
            content=f'New announcement in {classroom.name}: {data["title"]}',
            user_id=member.user_id,
            source_id=announcement.id
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'teacher': current_user.username
    })

@bp.route('/ping/teacher', methods=['POST'])
@login_required
def ping_teacher():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    if not teacher_id:
        # Try to find teacher by name or subject
        query = data.get('query', '').lower()
        teachers = User.query.filter_by(role='teacher').all()
        matching_teachers = []
        
        for teacher in teachers:
            if (query in teacher.username.lower() or 
                any(query in subject.lower() for subject in teacher.subjects)):
                matching_teachers.append(teacher)
        
        if not matching_teachers:
            return jsonify({'error': 'No matching teachers found'}), 404
        elif len(matching_teachers) > 1:
            return jsonify({
                'status': 'multiple_matches',
                'teachers': [{'id': t.id, 'name': t.username, 'subjects': t.subjects} 
                           for t in matching_teachers]
            })
        teacher_id = matching_teachers[0].id
    
    ping = TeacherPing(
        message=data['message'],
        student_id=current_user.id,
        teacher_id=teacher_id
    )
    
    # Create notification for teacher
    notification = Notification(
        type='ping',
        content=f'New ping from {current_user.username}: {data["message"][:50]}...',
        user_id=teacher_id,
        source_id=ping.id
    )
    
    db.session.add(ping)
    db.session.add(notification)
    db.session.commit()
    
    return jsonify(ping.to_dict())

@bp.route('/notifications')
@login_required
def view_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify([n.to_dict() for n in notifications])

@bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    data = request.get_json()
    notification_ids = data.get('notification_ids', [])
    
    notifications = Notification.query.filter(
        Notification.id.in_(notification_ids),
        Notification.user_id == current_user.id
    ).all()
    
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/ping/<int:ping_id>/respond', methods=['POST'])
@login_required
def respond_to_ping(ping_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    ping = TeacherPing.query.get_or_404(ping_id)
    if ping.teacher_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    ping.status = 'responded'
    
    # Create notification for student
    notification = Notification(
        type='ping_response',
        content=f'Teacher {current_user.username} responded to your ping: {data["response"][:50]}...',
        user_id=ping.student_id,
        source_id=ping.id
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify(ping.to_dict())
