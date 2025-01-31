from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.models.classroom import Classroom, ClassroomMember
from app import db
from datetime import datetime
import json

bp = Blueprint('quiz', __name__)

@bp.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if current_user.role != 'teacher':
        flash('Only teachers can create quizzes.', 'error')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        data = request.get_json()
        classroom_id = data.get('classroom_id')
        
        classroom = Classroom.query.get_or_404(classroom_id)
        if classroom.teacher_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        quiz = Quiz(
            title=data.get('title'),
            description=data.get('description'),
            difficulty=data.get('difficulty'),
            classroom_id=classroom_id,
            created_by=current_user.id,
            time_limit=data.get('time_limit'),
            passing_score=data.get('passing_score', 60)
        )
        
        try:
            db.session.add(quiz)
            db.session.flush()
            
            for q_data in data.get('questions', []):
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q_data.get('question_text'),
                    question_type=q_data.get('question_type'),
                    points=q_data.get('points', 1)
                )
                
                if q_data.get('question_type') == 'multiple_choice':
                    question.correct_answer = json.dumps(q_data.get('correct_answers', []))
                else:
                    question.correct_answer = q_data.get('correct_answer')
                    
                db.session.add(question)
                
            db.session.commit()
            return jsonify({'message': 'Quiz created successfully', 'quiz_id': quiz.id})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
            
    return render_template('quiz/create.html')

@bp.route('/quiz/<int:quiz_id>/take', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if student is in the classroom
    membership = ClassroomMember.query.filter_by(
        classroom_id=quiz.classroom_id,
        user_id=current_user.id
    ).first()
    
    if not membership:
        flash('You are not enrolled in this classroom.', 'error')
        return redirect(url_for('main.dashboard'))
        
    # Check for existing attempts
    existing_attempt = QuizAttempt.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id,
        completed_at=None
    ).first()
    
    if existing_attempt:
        if (datetime.utcnow() - existing_attempt.started_at).total_seconds() > quiz.time_limit * 60:
            existing_attempt.completed_at = datetime.utcnow()
            db.session.commit()
        else:
            return redirect(url_for('quiz.continue_quiz', attempt_id=existing_attempt.id))
            
    if request.method == 'POST':
        try:
            attempt = QuizAttempt(
                quiz_id=quiz_id,
                student_id=current_user.id
            )
            db.session.add(attempt)
            db.session.commit()
            
            return redirect(url_for('quiz.continue_quiz', attempt_id=attempt.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            
    return render_template('quiz/take.html', quiz=quiz)

@bp.route('/quiz/attempt/<int:attempt_id>', methods=['GET', 'POST'])
@login_required
def continue_quiz(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.student_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.dashboard'))
        
    if attempt.completed_at:
        return redirect(url_for('quiz.results', attempt_id=attempt_id))
        
    quiz = attempt.quiz
    if (datetime.utcnow() - attempt.started_at).total_seconds() > quiz.time_limit * 60:
        attempt.completed_at = datetime.utcnow()
        db.session.commit()
        flash('Time limit exceeded.', 'warning')
        return redirect(url_for('quiz.results', attempt_id=attempt_id))
        
    if request.method == 'POST':
        data = request.get_json()
        total_points = 0
        
        for answer_data in data.get('answers', []):
            question = QuizQuestion.query.get(answer_data.get('question_id'))
            if not question or question.quiz_id != quiz.id:
                continue
                
            answer = QuizAnswer(
                attempt_id=attempt_id,
                question_id=question.id,
                answer_text=json.dumps(answer_data.get('answer'))
            )
            
            if question.question_type == 'multiple_choice':
                correct_answers = set(json.loads(question.correct_answer))
                student_answers = set(answer_data.get('answer', []))
                answer.is_correct = correct_answers == student_answers
            else:
                answer.is_correct = answer_data.get('answer') == question.correct_answer
                
            answer.points_earned = question.points if answer.is_correct else 0
            total_points += answer.points_earned
            db.session.add(answer)
            
        attempt.completed_at = datetime.utcnow()
        attempt.score = (total_points / quiz.questions.count()) * 100
        
        try:
            db.session.commit()
            return jsonify({'message': 'Quiz submitted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
            
    return render_template('quiz/continue.html', attempt=attempt, quiz=quiz)

@bp.route('/quiz/results/<int:attempt_id>')
@login_required
def results(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.student_id != current_user.id and current_user.id != attempt.quiz.created_by:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.dashboard'))
        
    return render_template('quiz/results.html', attempt=attempt)

@bp.route('/quiz/<int:quiz_id>/stats')
@login_required
def quiz_stats(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if current_user.id != quiz.created_by:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.dashboard'))
        
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id, completed_at=None).all()
    stats = {
        'total_attempts': len(attempts),
        'average_score': sum(a.score for a in attempts if a.score) / len(attempts) if attempts else 0,
        'passing_rate': len([a for a in attempts if a.score >= quiz.passing_score]) / len(attempts) if attempts else 0
    }
    
    return render_template('quiz/stats.html', quiz=quiz, stats=stats)

@bp.route('/quizzes')
def list():
    return "Quizzes will be listed here"
