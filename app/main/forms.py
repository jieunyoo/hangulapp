from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, RadioField, IntegerField
from wtforms.validators import Required, Length, Email, Regexp, DataRequired
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    memberlevel = IntegerField('member')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class SubmitForm(FlaskForm):
    question = TextAreaField('question', validators=[DataRequired()])
    option1 = TextAreaField('A', validators=[DataRequired()])
    option2 = TextAreaField('B', validators=[DataRequired()])
    option3 = TextAreaField('C', validators=[DataRequired()])
    option4 = TextAreaField('D', validators=[DataRequired()])
    category = RadioField('category', 
        choices=[('numbers', 'numbers'), ('seasons', 'seasons'), ('pets', 'pets'),('months', 'months'), ('time', 'time'),('transportation', 'transportation'), ('fruit', 'fruit'), ('weekdays', 'weekdays')], validators = [DataRequired()])
    answer = RadioField('answer', 
        choices=[('option1', 'A'), ('option2', 'B'), ('option3', 'C'), ('option4', 'D')],
        validators = [DataRequired()])
    submit = SubmitField('Submit')

class QuizForm(FlaskForm):
    answer = SelectField('Answer', 
        choices=[('option1', 'A'), ('option2', 'B'), ('option3', 'C'), ('option4', 'D')],
        validators = [DataRequired()])
    #answer = SelectField('answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
     #   validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditForm(FlaskForm):
    question = TextAreaField('Question', validators=[DataRequired()])
    option1 = TextAreaField('A', validators=[DataRequired()])
    option2 = TextAreaField('B', validators=[DataRequired()])
    option3 = TextAreaField('C', validators=[DataRequired()])
    option4 = TextAreaField('D', validators=[DataRequired()])

    category = RadioField('category', 
        choices=[('numbers', 'numbers'), ('seasons', 'seasons'), ('pets', 'pets'), ('months', 'months'), ('time', 'time'),('transportation', 'transportation'), ('fruit', 'fruit'), ('weekdays', 'weekdays')], validators = [DataRequired()])
    answer = RadioField('answer', 
        choices=[('option1', 'A'), ('option2', 'B'), ('option3', 'C'), ('option4', 'D')],
        validators = [DataRequired()])
    submit = SubmitField('Submit')

