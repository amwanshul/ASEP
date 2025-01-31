from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.forum import ForumPost, ForumComment
from app.models.classroom import Classroom
from app.models.file_attachment import FileAttachment
from app.forms.forum import PostForm, CommentForm, ResolveForm, EscalateForm
from app import db
from werkzeug.utils import secure_filename
import os

bp = Blueprint('forum', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_attachment(file, post_id):
    if file and allowed_file(file.filename):
        if file.content_length and file.content_length > MAX_FILE_SIZE:
            return None, "File size exceeds maximum limit of 5MB"
        
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'attachments', str(post_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        attachment = FileAttachment(
            filename=filename,
            file_path=file_path,
            file_type=filename.rsplit('.', 1)[1].lower(),
            file_size=os.path.getsize(file_path),
            post_id=post_id,
            uploader_id=current_user.id
        )
        
        return attachment, None
    return None, "Invalid file type"

@bp.route('/forum')
@login_required
def index():
    try:
        if current_user.role == 'teacher':
            classrooms = current_user.classrooms_owned.all()
        else:
            classrooms = [m.classroom for m in current_user.memberships]
    
        classroom_ids = [c.id for c in classrooms]
        posts = ForumPost.query.filter(ForumPost.classroom_id.in_(classroom_ids)).order_by(ForumPost.created_at.desc()).all()
        return render_template('forum/index.html', posts=posts)
    except Exception as e:
        flash('An error occurred while loading the forum.', 'error')
        return render_template('forum/index.html', posts=[])

@bp.route('/forum/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if current_user.role == 'teacher':
        classrooms = current_user.classrooms_owned.all()
    else:
        classrooms = [m.classroom for m in current_user.memberships]
    
    form.classroom_id.choices = [(c.id, c.name) for c in classrooms]
    
    if form.validate_on_submit():
        classroom = Classroom.query.get_or_404(form.classroom_id.data)
        if current_user.role == 'teacher' and classroom not in current_user.classrooms_owned.all():
            flash('You do not have access to this classroom')
            return redirect(url_for('forum.index'))
        
        post = ForumPost(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id,
            classroom_id=form.classroom_id.data
        )
        
        db.session.add(post)
        db.session.flush()  # Get post ID for attachments
        
        files = request.files.getlist('attachments')
        for file in files:
            if file.filename:
                attachment, error = save_attachment(file, post.id)
                if attachment:
                    db.session.add(attachment)
                elif error:
                    flash(f'Error uploading {file.filename}: {error}')
        
        db.session.commit()
        
        flash('Your post has been created!')
        return redirect(url_for('forum.view_post', id=post.id))
    
    return render_template('forum/create_post.html', form=form)

@bp.route('/forum/post/<int:id>')
@login_required
def view_post(id):
    post = ForumPost.query.get_or_404(id)
    comment_form = CommentForm()
    resolve_form = ResolveForm()
    escalate_form = EscalateForm()
    
    # Check if teacher has access to the post's classroom
    if current_user.role == 'teacher' and post.classroom not in current_user.classrooms_owned.all():
        flash('You do not have access to this post')
        return redirect(url_for('forum.index'))
    # Check if student has access to the post's classroom
    if current_user.role == 'student' and post.classroom not in [m.classroom for m in current_user.memberships]:
        flash('You do not have access to this post')
        return redirect(url_for('forum.index'))
    
    return render_template('forum/view_post.html', 
                         post=post, 
                         comment_form=comment_form,
                         resolve_form=resolve_form,
                         escalate_form=escalate_form)

@bp.route('/forum/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    post = ForumPost.query.get_or_404(id)
    form = CommentForm()
    # Check if teacher has access to the post's classroom
    if current_user.role == 'teacher' and post.classroom not in current_user.classrooms_owned.all():
        flash('You do not have access to this post')
        return redirect(url_for('forum.index'))
    # Check if student has access to the post's classroom
    if current_user.role == 'student' and post.classroom not in [m.classroom for m in current_user.memberships]:
        flash('You do not have access to this post')
        return redirect(url_for('forum.index'))
    
    if form.validate_on_submit():
        comment = ForumComment(
            content=form.content.data,
            author_id=current_user.id,
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!')
    
    return redirect(url_for('forum.view_post', id=post.id))

@bp.route('/forum/post/<int:id>/vote', methods=['POST'])
@login_required
def vote_post(id):
    post = ForumPost.query.get_or_404(id)
    # Verify user has access to this post's classroom
    if current_user.role == 'teacher' and post.classroom not in current_user.classrooms_owned.all():
        return {'error': 'Access denied'}, 403
    if current_user.role == 'student' and post.classroom not in [m.classroom for m in current_user.memberships]:
        return {'error': 'Access denied'}, 403
    
    post.votes += 1
    db.session.commit()
    
    return {'votes': post.votes}

@bp.route('/forum/post/<int:id>/resolve', methods=['POST'])
@login_required
def mark_resolved(id):
    post = ForumPost.query.get_or_404(id)
    form = ResolveForm()
    
    if form.validate_on_submit():
        if current_user.id != post.author_id and current_user.role != 'teacher':
            flash('You do not have permission to mark this post as resolved')
            return redirect(url_for('forum.view_post', id=id))
        
        post.is_resolved = True
        db.session.commit()
        flash('Post marked as resolved!')
    
    return redirect(url_for('forum.view_post', id=id))

@bp.route('/forum/post/<int:id>/escalate', methods=['POST'])
@login_required
def escalate(id):
    post = ForumPost.query.get_or_404(id)
    form = EscalateForm()
    
    if form.validate_on_submit():
        if current_user.role != 'teacher':
            flash('Only teachers can escalate posts')
            return redirect(url_for('forum.view_post', id=id))
        
        post.is_escalated = True
        db.session.commit()
        flash('Post has been escalated!')
    
    return redirect(url_for('forum.view_post', id=id))

@bp.route('/forum/attachment/<int:id>')
@login_required
def download_attachment(id):
    attachment = FileAttachment.query.get_or_404(id)
    
    # Check if user has access to the post's classroom
    post = attachment.post
    if current_user not in post.classroom.members and current_user != post.classroom.teacher:
        flash('You do not have permission to access this file')
        return redirect(url_for('main.dashboard'))
    
    return send_file(
        attachment.file_path,
        as_attachment=True,
        download_name=attachment.filename
    )
