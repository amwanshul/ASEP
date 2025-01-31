from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.classroom import Classroom, ClassroomMember, Resource
from app.models.user import User
from app.models.quiz import Quiz
from app.models.announcement import Announcement
from app import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    try:
        user_data = {
            'username': current_user.username,
            'role': current_user.role,
            'points': current_user.points or 0,
            'full_name': current_user.full_name
        }
        
        if current_user.role == 'teacher':
            classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
            return render_template(
                'dashboard.html',
                user=user_data,
                classrooms=classrooms,
                is_teacher=True
            )
        else:
            memberships = ClassroomMember.query.filter_by(user_id=current_user.id).all()
            classrooms = []
            for membership in memberships:
                try:
                    classroom = Classroom.query.get(membership.classroom_id)
                    if classroom:
                        classrooms.append(classroom)
                except Exception:
                    continue
                    
            return render_template(
                'dashboard.html',
                user=user_data,
                classrooms=classrooms,
                memberships=memberships,
                is_teacher=False,
                classes_joined=len(classrooms)
            )
            
    except Exception as e:
        print(f"Dashboard error: {str(e)}")  # For debugging
        flash('An error occurred while loading the dashboard. Please try again.', 'error')
        return render_template(
            'dashboard.html',
            user={
                'username': current_user.username,
                'role': current_user.role,
                'points': 0,
                'full_name': current_user.full_name
            },
            classrooms=[],
            memberships=[],
            is_teacher=(current_user.role == 'teacher'),
            classes_joined=0
        )

@bp.route('/join-class', methods=['POST'])
@login_required
def join_class():
    if current_user.role == 'teacher':
        flash('Teachers cannot join classes.', 'error')
        return redirect(url_for('classroom.list'))
        
    class_code = request.form.get('class_code')
    if not class_code:
        flash('Please provide a class code.', 'error')
        return redirect(url_for('classroom.list'))
        
    # Find classroom by code
    classroom = Classroom.query.filter_by(code=class_code).first()
    if not classroom:
        flash('Invalid class code. Please check and try again.', 'error')
        return redirect(url_for('classroom.list'))
        
    # Check if already enrolled
    existing = ClassroomMember.query.filter_by(
        classroom_id=classroom.id,
        user_id=current_user.id
    ).first()
    
    if existing:
        flash('You are already enrolled in this class.', 'info')
        return redirect(url_for('classroom.list'))
        
    try:
        # Add student to classroom
        membership = ClassroomMember(
            classroom_id=classroom.id,
            user_id=current_user.id
        )
        db.session.add(membership)
        db.session.commit()
        flash('Successfully joined the classroom!', 'success')
        return redirect(url_for('classroom.list'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while joining the classroom. Please try again.', 'error')
        return redirect(url_for('classroom.list'))

@bp.route('/classroom/create', methods=['GET', 'POST'])
@login_required
def create_classroom():
    if current_user.role != 'teacher':
        flash('Only teachers can create classrooms.', 'error')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        description = request.form.get('description')
        
        if not name or not subject:
            flash('Classroom name and subject are required.', 'error')
            return render_template('main/create_classroom.html')
            
        try:
            # Generate a unique class code
            code = generate_class_code()
            classroom = Classroom(
                name=name,
                subject=subject,
                description=description,
                teacher_id=current_user.id,
                code=code
            )
            db.session.add(classroom)
            db.session.commit()
            flash('Classroom created successfully! Class code: ' + code, 'success')
            return redirect(url_for('main.view_classroom', classroom_id=classroom.id))
        except Exception as e:
            db.session.rollback()
            flash('Error creating classroom. Please try again.', 'error')
            
    return render_template('main/create_classroom.html')

def generate_class_code(length=6):
    """Generate a random class code."""
    import random
    import string
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        # Check if code already exists
        if not Classroom.query.filter_by(code=code).first():
            return code

@bp.route('/classroom/<int:classroom_id>')
@login_required
def view_classroom(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Check if user has access to this classroom
    if current_user.role == 'teacher':
        if classroom.teacher_id != current_user.id:
            flash('You do not have access to this classroom.', 'error')
            return redirect(url_for('main.dashboard'))
    else:
        membership = ClassroomMember.query.filter_by(
            user_id=current_user.id,
            classroom_id=classroom_id
        ).first()
        if not membership:
            flash('You are not enrolled in this classroom.', 'error')
            return redirect(url_for('main.dashboard'))
            
    # Get classroom resources and quizzes
    resources = Resource.query.filter_by(classroom_id=classroom_id).all()
    quizzes = Quiz.query.filter_by(classroom_id=classroom_id).all()
    
    return render_template('main/classroom.html',
                         classroom=classroom,
                         resources=resources,
                         quizzes=quizzes,
                         is_teacher=(current_user.role == 'teacher'))

@bp.route('/classroom/<int:classroom_id>/join', methods=['POST'])
@login_required
def join_classroom(classroom_id):
    if current_user.role != 'student':
        flash('Only students can join classrooms.', 'error')
        return redirect(url_for('main.dashboard'))
        
    classroom = Classroom.query.get_or_404(classroom_id)
    
    existing_membership = ClassroomMember.query.filter_by(
        classroom_id=classroom_id,
        user_id=current_user.id
    ).first()
    
    if existing_membership:
        flash('You are already enrolled in this classroom.', 'info')
        return redirect(url_for('main.view_classroom', classroom_id=classroom_id))
        
    membership = ClassroomMember(
        classroom_id=classroom_id,
        user_id=current_user.id,
        role='student'
    )
    
    try:
        db.session.add(membership)
        db.session.commit()
        flash('Successfully joined the classroom!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        
    return redirect(url_for('main.view_classroom', classroom_id=classroom_id))

@bp.route('/classroom/<int:classroom_id>/leave', methods=['POST'])
@login_required
def leave_classroom(classroom_id):
    if current_user.role != 'student':
        flash('Only students can leave classrooms.', 'error')
        return redirect(url_for('main.dashboard'))
        
    membership = ClassroomMember.query.filter_by(
        classroom_id=classroom_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        db.session.delete(membership)
        db.session.commit()
        flash('Successfully left the classroom.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        
    return redirect(url_for('main.dashboard'))

@bp.route('/classroom/<int:classroom_id>/upload', methods=['POST'])
@login_required
def upload_resource(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    
    if current_user.id != classroom.teacher_id:
        flash('Only teachers can upload resources.', 'error')
        return redirect(url_for('main.view_classroom', classroom_id=classroom_id))
        
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('main.view_classroom', classroom_id=classroom_id))
        
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('main.view_classroom', classroom_id=classroom_id))
        
    if not allowed_file(file.filename):
        flash('File type not allowed.', 'error')
        return redirect(url_for('main.view_classroom', classroom_id=classroom_id))
        
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join('app', 'static', 'uploads', filename)
        file.save(file_path)
        
        resource = Resource(
            title=request.form.get('title', filename),
            description=request.form.get('description', ''),
            file_path=filename,
            resource_type=file.filename.rsplit('.', 1)[1].lower(),
            classroom_id=classroom_id,
            uploaded_by=current_user.id
        )
        
        db.session.add(resource)
        db.session.commit()
        flash('Resource uploaded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while uploading the resource.', 'error')
        
    return redirect(url_for('main.view_classroom', classroom_id=classroom_id))

@bp.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html', user=current_user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.bio = request.form.get('bio')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            
    return render_template('main/edit_profile.html', user=current_user)
