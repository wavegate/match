from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User
from wtforms.fields.html5 import DateField

class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))

class AddInterviewForm(FlaskForm):
    date = DateField('Date invite was received', validators=[DataRequired()])
    supplemental_required = BooleanField()
    method = SelectField('How was the interview offered?', choices=['ERAS','Thalamus','Email'])
    submit = SubmitField(_l('Submit'))

    def __init__(self, user, program, *args, **kwargs):
        super(AddInterviewForm, self).__init__(*args, **kwargs)
        self.program = program
        self.user = user

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField(_l('Enter interview review:'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

class ProgramForm(FlaskForm):
    name = StringField(_l('Add Program Name'), validators=[DataRequired()])
    body = TextAreaField(_l('Enter interview format'))
    image = StringField(_l('Image link:'))
    submit = SubmitField('Submit')