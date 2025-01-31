from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class PostForm(FlaskForm):
    classroom_id = SelectField('Classroom', validators=[DataRequired()], coerce=int)
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])

class CommentForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])

class ResolveForm(FlaskForm):
    pass

class EscalateForm(FlaskForm):
    pass
