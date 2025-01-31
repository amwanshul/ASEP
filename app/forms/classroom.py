from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional, Length

class ClassroomRequestForm(FlaskForm):
    message = TextAreaField('Message (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Request to Join')

class ClassroomResponseForm(FlaskForm):
    response_message = TextAreaField('Response Message (Optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Response')
