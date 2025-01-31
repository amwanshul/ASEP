from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from app.models.classroom import Classroom, ClassroomMember
from app.models.user import User
from app.models.classroom_request import ClassroomRequest
from app.forms.classroom import ClassroomRequestForm, ClassroomResponseForm
from app import db
from datetime import datetime

bp = Blueprint('classroom', __name__)

class ClassroomForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])

class JoinClassForm(FlaskForm):
    class_code = StringField('Class Code', validators=[DataRequired()])

@bp.route('/classrooms')
@login_required
def list():
    try:
        if current_user.role == 'teacher':
            # Teachers see their own classrooms
            classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
            joined_classrooms = set()  # Teachers don't need to join their own classes
        else:
            # Students see all available classrooms
            classrooms = Classroom.query.all()
            # Get the IDs of classrooms the student has already joined
            memberships = ClassroomMember.query.filter_by(user_id=current_user.id).all()
            joined_classrooms = {m.classroom_id for m in memberships}
        
        form = JoinClassForm()
        return render_template('classroom/list.html', 
                             classrooms=classrooms,
                             joined_classrooms=joined_classrooms,
                             form=form)
    except Exception as e:
        flash('An error occurred while loading classrooms.', 'error')
        form = JoinClassForm()
        return render_template('classroom/list.html', 
                             classrooms=[],
                             joined_classrooms=set(),
                             form=form)

@bp.route('/classroom/join-by-code', methods=['POST'])
@login_required
def join_by_code():
    if current_user.role == 'teacher':
        flash('Teachers cannot join classrooms', 'error')
        return redirect(url_for('classroom.list'))
    
    form = JoinClassForm()
    if form.validate_on_submit():
        class_code = form.class_code.data.strip().upper()
        classroom = Classroom.query.filter_by(code=class_code).first()
        
        if not classroom:
            flash('Invalid class code. Please check and try again.', 'error')
            return redirect(url_for('classroom.list'))
        
        # Check if already a member
        existing_member = ClassroomMember.query.filter_by(
            user_id=current_user.id,
            classroom_id=classroom.id
        ).first()
        
        if existing_member:
            flash('You are already a member of this classroom', 'warning')
            return redirect(url_for('classroom.view', id=classroom.id))
        
        # Check if there's a pending request
        existing_request = ClassroomRequest.query.filter_by(
            user_id=current_user.id,
            classroom_id=classroom.id,
            status='pending'
        ).first()
        
        if existing_request:
            flash('You already have a pending request for this classroom', 'info')
            return redirect(url_for('classroom.list'))
        
        # Create join request
        request = ClassroomRequest(
            user_id=current_user.id,
            classroom_id=classroom.id
        )
        db.session.add(request)
        db.session.commit()
        
        flash('Your request to join the classroom has been sent', 'success')
        return redirect(url_for('classroom.list'))
    
    flash('Invalid form submission. Please try again.', 'error')
    return redirect(url_for('classroom.list'))

@bp.route('/classroom/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'teacher':
        flash('Only teachers can create classrooms', 'error')
        return redirect(url_for('classroom.list'))
    
    form = ClassroomForm()
    if form.validate_on_submit():
        classroom = Classroom(
            name=form.name.data,
            subject=form.subject.data,
            description=form.description.data,
            teacher_id=current_user.id,
            code=Classroom.generate_class_code()
        )
        db.session.add(classroom)
        db.session.commit()
        flash('Classroom created successfully!', 'success')
        return redirect(url_for('classroom.view', id=classroom.id))
    
    return render_template('classroom/create.html', form=form)

@bp.route('/classroom/<int:id>')
@login_required
def view(id):
    classroom = Classroom.query.get_or_404(id)
    
    # Check if user has access
    if current_user.role == 'teacher':
        if classroom.teacher_id != current_user.id:
            flash('You do not have access to this classroom', 'error')
            return redirect(url_for('classroom.list'))
    else:
        member = ClassroomMember.query.filter_by(
            user_id=current_user.id,
            classroom_id=id
        ).first()
        if not member:
            flash('You do not have access to this classroom', 'error')
            return redirect(url_for('classroom.list'))
    
    return render_template('classroom/view.html', classroom=classroom)

@bp.route('/classroom/<int:id>/manage')
@login_required
def manage(id):
    classroom = Classroom.query.get_or_404(id)
    if current_user.role != 'teacher' or classroom.teacher_id != current_user.id:
        flash('You do not have permission to manage this classroom', 'error')
        return redirect(url_for('classroom.list'))
    
    return render_template('classroom/manage.html', classroom=classroom)

@bp.route('/classroom/<int:id>/request', methods=['GET', 'POST'])
@login_required
def request_join(id):
    if current_user.role == 'teacher':
        flash('Teachers cannot request to join classrooms', 'error')
        return redirect(url_for('classroom.list'))
    
    classroom = Classroom.query.get_or_404(id)
    
    # Check if already a member
    existing_member = ClassroomMember.query.filter_by(
        user_id=current_user.id,
        classroom_id=id
    ).first()
    
    if existing_member:
        flash('You are already a member of this classroom', 'warning')
        return redirect(url_for('classroom.view', id=id))
    
    # Check if there's a pending request
    existing_request = ClassroomRequest.query.filter_by(
        user_id=current_user.id,
        classroom_id=id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You already have a pending request for this classroom', 'info')
        return redirect(url_for('classroom.list'))
    
    form = ClassroomRequestForm()
    if request.method == 'POST':
        request_obj = ClassroomRequest(
            user_id=current_user.id,
            classroom_id=id
        )
        db.session.add(request_obj)
        db.session.commit()
        
        flash('Your request to join the classroom has been sent', 'success')
        return redirect(url_for('classroom.list'))
    
    return render_template('classroom/request_join.html', classroom=classroom, form=form)

@bp.route('/classroom/requests')
@login_required
def view_requests():
    if current_user.role != 'teacher':
        flash('Only teachers can view classroom requests', 'error')
        return redirect(url_for('classroom.list'))
    
    # Get all pending requests for classrooms where the current user is the teacher
    pending_requests = ClassroomRequest.query.join(Classroom).filter(
        Classroom.teacher_id == current_user.id,
        ClassroomRequest.status == 'pending'
    ).order_by(ClassroomRequest.created_at.desc()).all()
    
    approve_form = ClassroomResponseForm()
    reject_form = ClassroomResponseForm()
    
    return render_template('classroom/view_requests.html', 
                         requests=pending_requests,
                         approve_form=approve_form,
                         reject_form=reject_form)

@bp.route('/classroom/request/<int:id>/approve', methods=['POST'])
@login_required
def approve_request(id):
    request_obj = ClassroomRequest.query.get_or_404(id)
    
    # Verify that the current user is the teacher of the classroom
    if request_obj.classroom.teacher_id != current_user.id:
        flash('You do not have permission to approve this request', 'error')
        return redirect(url_for('classroom.view_requests'))
    
    form = ClassroomResponseForm()
    if form.validate_on_submit():
        # Create new classroom membership
        member = ClassroomMember(
            user_id=request_obj.user_id,
            classroom_id=request_obj.classroom_id,
            role='student'
        )
        db.session.add(member)
        
        # Update request status
        request_obj.status = 'approved'
        request_obj.response_message = form.response_message.data
        request_obj.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Request approved successfully', 'success')
    
    return redirect(url_for('classroom.view_requests'))

@bp.route('/classroom/request/<int:id>/reject', methods=['POST'])
@login_required
def reject_request(id):
    request_obj = ClassroomRequest.query.get_or_404(id)
    
    # Verify that the current user is the teacher of the classroom
    if request_obj.classroom.teacher_id != current_user.id:
        flash('You do not have permission to reject this request', 'error')
        return redirect(url_for('classroom.view_requests'))
    
    form = ClassroomResponseForm()
    if form.validate_on_submit():
        request_obj.status = 'rejected'
        request_obj.response_message = form.response_message.data
        request_obj.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Request rejected', 'success')
    
    return redirect(url_for('classroom.view_requests'))
