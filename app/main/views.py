from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, SubmitForm, QuizForm, EditForm
from .. import db
from ..models import Permission, Role, User, Questions, Quiz
from ..decorators import admin_required, permission_required
from pickle import loads, dumps
import json
import os
import stripe
import datetime
from sqlalchemy.sql import func

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['QUIZ_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response

@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', user=user)

@main.route('/welcome', methods=['GET', 'POST'])
def welcome():
    return render_template('welcome.html', user=user)

#USER---------------------------------------------------------------------------------------
@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    quizscoreslist = Quiz.query.order_by(Quiz.id.desc())
    return render_template('user.html', user=user,quizscoreslist=quizscoreslist)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        user.memberlevel = form.memberlevel.data
        db.session.add(user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    form.memberlevel.data = user.memberlevel
    return render_template('edit_profile.html', form=form, user=user)


#QUESTION SUBMISSION---------------------------------------------------------------------------------------
@main.route('/submit', methods=['GET', 'POST'])
@login_required
@admin_required
def submit():
    form = SubmitForm()
    if form.validate_on_submit():
        questiondata = Questions( 
            question = form.question.data, 
            option1=form.option1.data,
            option2=form.option2.data,
            option3=form.option3.data,
            option4=form.option4.data,
            category=form.category.data,
            answer=form.answer.data)
        db.session.add(questiondata)
        db.session.commit()
        flash('thanks')
        return render_template('submit.html', form=form, user=user)
    return render_template('submit.html', form=form, user=user)


@main.route('/edit/<int:questionid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(questionid):
    toedit = Questions.query.get_or_404(questionid)
    form = EditForm()
    if form.validate_on_submit():
        toedit.question = form.question.data
        toedit.option1 = form.option1.data
        toedit.option2 = form.option2.data
        toedit.option3 = form.option3.data
        toedit.option4 = form.option4.data
        toedit.answer = form.answer.data
        toedit.category = form.category.data
        db.session.add(toedit)
        flash('thanks')
        return redirect(url_for('.edit', questionid=toedit.questionid))
    form.question.data = toedit.question
    form.option1.data = toedit.option1
    form.option2.data = toedit.option2
    form.option3.data = toedit.option3
    form.option4.data = toedit.option4
    form.answer.data = toedit.answer
    form.category.data = toedit.category
    return render_template('edit.html', form=form, user=user)


#general ---------------------------------------------------------------------------------------
@main.route('/upgrade', methods=['GET'])
def upgrade():
    page = request.args.get('page', 1, type=int)
    return render_template('upgrade.html', title='upgrade', key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

@main.route('/help', methods=['GET'])
def help():
    page = request.args.get('page', 1, type=int)
    return render_template('help.html', title='help')

@main.route('/results/<int:quizid>', methods=['GET'])
@login_required
def results(quizid):
    getthequiz = Quiz.query.filter_by(id=quizid).first()
    score=getthequiz.quizscore
    points=getthequiz.countquestions
    return render_template('results.html',score=score,points=points)

@main.route('/delete/<int:id>')
@login_required
def delete(id):
    user = current_user
    userid = user.id
    if user.memberlevel == 2:
        quizid = Quiz.query.filter_by(id=id).first()
        #protects against random users deleting other user's things
        if userid == quizid.user_id:
            if user.quizcount:
                user.quizcount -= 1
                db.session.delete(quizid)
                db.session.add(user)
                db.session.commit()
                flash('The quiz grade was deleted.')
        else:
            flash('error')
        return redirect(url_for('.user',username=user.username))
    else:
        return redirect(url_for('.user', username=user.username))

@main.route('/learn', methods=['GET'])
def learn():
    return render_template('learn.html', title='learn')


@main.route('/hangul/<string:category>/<int:quizid>/<int:questionid>', methods=['GET','POST'])
@login_required
def hangul(category,quizid,questionid):
    check = Questions.query.get_or_404(questionid)
    username = current_user.username
    user = User.query.filter_by(username=username).first()
    correctAnswer = check.answer
    questionid=questionid
    quizid=quizid
    category=category
    #quizzeslist = Quiz.query.join(User).filter(User.id == current_user.id)
    getthequiz = Quiz.query.filter_by(id=quizid).first()
    savethisscore=getthequiz.quizscore
    savecountpoints=getthequiz.countquestions

    form = QuizForm()
    if getthequiz.answered is None:
        getthequiz.answered = dumps([])
    else:
        alreadyAns = loads(getthequiz.answered)

    if form.validate_on_submit():
        enteredData = form.answer.data
        if questionid in alreadyAns:
            flash('you already answered this')
            getnextquestion = Questions.query.filter_by(category=category).filter(~Questions.questionid.in_(alreadyAns)).first()
            if getnextquestion == None:
                return redirect(url_for('.results',quizid=quizid))
            else:
                questionid = getnextquestion.questionid
            return redirect(url_for('.hangul', user=current_user, questionid=questionid,quizid=quizid,category=category))

        if enteredData == correctAnswer:
            savecountpoints += 1
            getthequiz.countquestions = savecountpoints
            flash('good job!')
            savethisscore += 1
            getthequiz.quizscore = savethisscore

            db.session.add(getthequiz)
            alreadyAns.append(questionid)
            getthequiz.answered=dumps(alreadyAns)
            db.session.commit()
        else:
            flash('sorry - incorrect - please try again')
            savecountpoints += 1
            getthequiz.countquestions=savecountpoints
            db.session.add(getthequiz)
            db.session.commit()

        getnextquestion = Questions.query.filter_by(category=category).filter(~Questions.questionid.in_(alreadyAns)).order_by(func.random()).first()
        if getnextquestion == None:
            return redirect(url_for('.results',quizid=quizid))
        else:
            questionid = getnextquestion.questionid
            return redirect(url_for('.hangul', user=current_user, questionid=questionid,quizid=quizid,category=category))
    return render_template('hangul.html', form=form, user=current_user, check=check, questionid=questionid,quizid=quizid,category=category)



#Admin SUBMISSION---------------------------------------------------------------------------------------
@main.route('/adminscores',methods=['GET'])
@login_required
@admin_required
def adminscores():
    quizscoreslist = Quiz.query.order_by(Quiz.id.desc())
    return render_template('adminscores.html', title='adminscores',quizscoreslist=quizscoreslist)


@main.route('/adminquestions',methods=['GET'])
@login_required
@admin_required
def adminquestions():
    quizquestions = Questions.query.all()
    return render_template('adminquestions.html', title='adminquestions',quizquestions=quizquestions)


#try STRIPE _____________________________________________________________________
@main.route('/charge',methods=['POST'])
@login_required
def charge():
    amount = 200
    user = current_user
    useremail = user.email
    customer = stripe.Customer.create(
        email=useremail,
        source=request.form['stripeToken']
        )
    charge = stripe.Charge.create(
        customer = customer.id,
        amount = amount,
        currency = 'usd',
        description='flask test charge'
        )
    user = current_user
    user.memberlevel = 2
    user.memberexpirationdate = datetime.date.today()
    db.session.add(user)
    db.session.commit()
    return render_template('charge.html',amount=amount)




#quizzes -------------------------------------------------------------------
@main.route('/numbers')
@login_required
def numbers():
    category='numbers'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
        if user.quizcount > 4:
            flash('the free version is limited to 5 quizzes - consider upgrading your membership')
            return redirect(url_for('.index'))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))

@main.route('/seasons')
@login_required
def seasons():
    category='seasons'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
        if user.quizcount > 4:
            flash('the free version is limited to 5 quizzes - consider upgrading your membership')
            return redirect(url_for('.index'))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))


@main.route('/pets')
@login_required
def pets():
    category='pets'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
            flash('please sign up for a membership')
            return redirect(url_for('.index'))


@main.route('/timequiz')
@login_required
def timequiz():
    category='time'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
            flash('please sign up for a membership')
            return redirect(url_for('.index'))


@main.route('/months')
@login_required
def months():
    category='months'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
            flash('please sign up for a membership')
            return redirect(url_for('.index'))

@main.route('/transportation')
@login_required
def transportation():
    category='transportation'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
            flash('please sign up for a membership')
            return redirect(url_for('.index'))


@main.route('/fruit')
@login_required
def fruit():
    category='fruit'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
            flash('please sign up for a membership')
            return redirect(url_for('.index'))



@main.route('/weekdays')
@login_required
def weekdays():
    category='weekdays'
    user = current_user
    if user.quizcount is None:
        user.quizcount = 1
    if user.memberlevel == 2:
        if user.quizcount > 20:
            flash('sorry, you can only attempt & save 5 quiz scores - but, if you delete some past quiz scores, you may continue')
            return redirect(url_for('.user', username=user.username))
        else:
            user.quizcount += 1
            startfirstquiz = Quiz(author=current_user,quizscore=0,countquestions=0,quizname=category,user_id=user.id)
            db.session.add(startfirstquiz)
            db.session.add(user)
            db.session.commit()
            firstquestiontoshow=Questions.query.filter_by(category=category).first()
            questionid=firstquestiontoshow.questionid
            quizid=startfirstquiz.id
            myquizscore=startfirstquiz.quizscore
            return redirect(url_for('.hangul',quizid=quizid,questionid=questionid,category=category))
    else:
            flash('please sign up for a membership')
            return redirect(url_for('.index'))
