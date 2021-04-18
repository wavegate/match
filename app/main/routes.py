from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
	jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db, csrf
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm, ProgramForm, AddInterviewForm, FeedbackForm, SLUMSForm
from app.models import User, Post, Program, Message, Notification, Interview, Interview_Date, Test
from app.translate import translate
from app.main import bp
from app.auth.email import send_feedback_email
from app.nocache import nocache
import logging
import re
import flask_excel as excel
import pandas as pd
import datetime as dt
import dateutil.parser
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os
import base64
import json
import glob
import dateparser
import math

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
	if current_user.is_authenticated:
		return redirect(url_for('main.user', username=current_user.username))
	else:
		return redirect(url_for('main.programs'))

#@bp.before_app_request
#def before_request():
#	if current_user.is_authenticated:
#		current_user.last_seen = datetime.utcnow()
#		db.session.commit()
#		g.search_form = SearchForm()
#	g.locale = str(get_locale())

@bp.route('/programs', methods=['GET', 'POST'])
def programs():
	form = ProgramForm()
	if form.validate_on_submit():
		program = Program(name=form.name.data, specialty=form.specialty.data, body=form.body.data, image=form.image.data, state=form.state.data)
		db.session.add(program)
		db.session.commit()
		flash(_('Program added!'))
		return redirect(url_for('main.programs'))
	programs = Program.query.order_by(Program.timestamp.desc())
	return render_template('programs.html', title=_('Programs'),
						   programs=programs, form=form)

@bp.route('/program/<name>', methods=['GET','POST'])
@login_required
def program(name):
	program = Program.query.filter_by(name=name).first_or_404()
	interviews = program.interviews.order_by(Interview.date.desc())
	page = request.args.get('page', 1, type=int)
	postform = PostForm()
	if postform.validate_on_submit():
		language = guess_language(postform.post.data)
		if language == 'UNKNOWN' or len(language) > 5:
			language = ''
		post = Post(body=postform.post.data, author=current_user,
					language=language, program=program)
		db.session.add(post)
		db.session.commit()
		flash(_('Your post is now live!'))
		return redirect(url_for('main.program', name=name))
	posts = program.posts.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.program', name=name,
					   page=posts.next_num) if posts.has_next else None
	prev_url = url_for('main.program', name=name,
					   page=posts.prev_num) if posts.has_prev else None
	form = EmptyForm()
	return render_template('program.html', next_url=next_url, prev_url=prev_url,program=program, interviews=program.interviews, postform=postform, form=form, posts=posts.items)

@bp.route('/delete_post/<int:post>?program=<program>', methods=['GET','POST'])
@login_required
def delete_post(post, program):
	#flash(program)
	post = Post.query.get(post)
	db.session.delete(post)
	db.session.commit()
	flash('Post deleted!')
	#return redirect(url_for('main.index'))
	return redirect(url_for('main.program',name=program))

@bp.route('/add_interview/<name>', methods=['GET', 'POST'])
@login_required
def add_interview(name):
	program = Program.query.filter_by(name=name).first_or_404()
	form = AddInterviewForm(current_user.username, program)
	if form.validate_on_submit():
		interview = Interview(date=form.date.data,interviewer=program,interviewee=current_user, supplemental_required=form.supplemental_required.data, method=form.method.data)
		dates = None
		dates2 = None
		if request.form['dates'] != '':
			available_dates = list(map(lambda x:datetime.strptime(x, '%m/%d/%Y'), request.form['dates'].split(',')))
			dates = list(map(lambda x: Interview_Date(date=x, interviewer=program,interviewee=current_user, invite=interview,full=False), available_dates))
		if request.form['unavailable_dates'] != '':
			unavailable_dates = list(map(lambda x:datetime.strptime(x, '%m/%d/%Y'), request.form['unavailable_dates'].split(',')))
			dates2 = list(map(lambda x: Interview_Date(date=x, interviewer=program,interviewee=current_user, invite=interview,full=True), unavailable_dates))
		if dates:
			interview.dates = dates
		if dates2:
			interview.dates = dates2
		if dates and dates2:
			interview.dates = dates + dates2
		if not current_user.is_following_program(program):
			current_user.follow_program(program)
		db.session.add(interview)
		db.session.commit()
		flash(_('Interview added!'))
		return redirect(url_for('main.program', name=name))
	return render_template('add_interview.html',title=_('Add Interview Offer'),
						   form=form, program=program)

@bp.route('/delete_interview/<int:interview>', methods=['POST'])
@login_required
def delete_interview(interview):
	interview = Interview.query.get(interview)
	program = interview.interviewer
	db.session.delete(interview)
	db.session.commit()
	return redirect(url_for('main.program', name=program.name))

@bp.route('/user/<username>', methods=['GET','POST'])
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.user', username=user.username,
					   page=posts.next_num) if posts.has_next else None
	prev_url = url_for('main.user', username=user.username,
					   page=posts.prev_num) if posts.has_prev else None
	form = EditProfileForm(current_user.username)
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		db.session.commit()
		flash(_('Your changes have been saved.'))
		return render_template('user.html', user=user, interviews=user.interviews,posts=posts.items,next_url=next_url,prev_url=prev_url,form=form)
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
	return render_template('user.html', user=user, interviews=user.interviews,posts=posts.items, programs=user.programs,
						   next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm(current_user.username)
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		db.session.commit()
		flash(_('Your changes have been saved.'))
		return redirect(url_for('main.edit_profile'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', title=_('Edit Profile'),
						   form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
	form = EmptyForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user is None:
			flash(_('User %(username)s not found.', username=username))
			return redirect(url_for('main.programs'))
		if user == current_user:
			flash(_('You cannot follow yourself!'))
			return redirect(url_for('main.user', username=username))
		current_user.follow(user)
		db.session.commit()
		flash(_('You are following %(username)s!', username=username))
		return redirect(url_for('main.user', username=username))
	else:
		return redirect(url_for('main.programs'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
	form = EmptyForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=username).first()
		if user is None:
			flash(_('User %(username)s not found.', username=username))
			return redirect(url_for('main.programs'))
		if user == current_user:
			flash(_('You cannot unfollow yourself!'))
			return redirect(url_for('main.user', username=username))
		current_user.unfollow(user)
		db.session.commit()
		flash(_('You are not following %(username)s.', username=username))
		return redirect(url_for('main.user', username=username))
	else:
		return redirect(url_for('main.programs'))

@bp.route('/follow_program/<name>', methods=['POST'])
@login_required
def follow_program(name):
	form = EmptyForm()
	if form.validate_on_submit():
		program = Program.query.filter_by(name=name).first()
		if program is None:
			flash(_('Program %(name)s not found.', name=name))
			return redirect(url_for('main.programs'))
		current_user.follow_program(program)
		db.session.commit()
		flash(_('You are following %(name)s!', name=name))
		return redirect(url_for('main.program', name=name))
	else:
		return redirect(url_for('main.programs'))

@bp.route('/unfollow_program/<name>', methods=['POST'])
@login_required
def unfollow_program(name):
	form = EmptyForm()
	if form.validate_on_submit():
		program = Program.query.filter_by(name=name).first()
		if program is None:
			flash(_('Program %(name)s not found.', name=name))
			return redirect(url_for('main.programs'))
		current_user.unfollow_program(program)
		db.session.commit()
		flash(_('You are not following %(name)s.', name=name))
		return redirect(url_for('main.program', name=name))
	else:
		return redirect(url_for('main.programs'))

@bp.route('/delete_program/<name>', methods=['POST'])
@login_required
def delete_program(name):
	program = Program.query.filter_by(name=name).first()
	db.session.delete(program)
	db.session.commit()
	flash(_('Program deleted!'))
	return redirect(url_for('main.programs'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
	return jsonify({'text': translate(request.form['text'],
									  request.form['source_language'],
									  request.form['dest_language'])})


#@bp.route('/search')
#@login_required
#def search():
#	if not g.search_form.validate():
#		return redirect(url_for('main.explore'))
#	page = request.args.get('page', 1, type=int)
#	posts, total = Post.search(g.search_form.q.data, page,
#							   current_app.config['POSTS_PER_PAGE'])
#	next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
#		if total > page * current_app.config['POSTS_PER_PAGE'] else None
#	prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
#		if page > 1 else None
#	return render_template('search.html', title=_('Search'), posts=posts,
#						   next_url=next_url, prev_url=prev_url)

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
	user = User.query.filter_by(username=username).first_or_404()
	form = EmptyForm()
	return render_template('user_popup.html', user=user, form=form)

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
	user = User.query.filter_by(username=recipient).first_or_404()
	form = MessageForm()
	if form.validate_on_submit():
		msg = Message(author=current_user, recipient=user,
					  body=form.message.data)
		db.session.add(msg)
		user.add_notification('unread_message_count', user.new_messages())
		db.session.commit()
		flash(_('Your message has been sent.'))
		return redirect(url_for('main.user', username=recipient))
	return render_template('send_message.html', title=_('Send Message'),
						   form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
	current_user.last_message_read_time = datetime.utcnow()
	current_user.add_notification('unread_message_count', 0)
	db.session.commit()
	page = request.args.get('page', 1, type=int)
	messages = current_user.messages_received.order_by(
		Message.timestamp.desc()).paginate(
			page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.messages', page=messages.next_num) \
		if messages.has_next else None
	prev_url = url_for('main.messages', page=messages.prev_num) \
		if messages.has_prev else None
	return render_template('messages.html', messages=messages.items,
						   next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
	since = request.args.get('since', 0.0, type=float)
	notifications = current_user.notifications.filter(
		Notification.timestamp > since).order_by(Notification.timestamp.asc())
	return jsonify([{
		'name': n.name,
		'data': n.get_data(),
		'timestamp': n.timestamp
	} for n in notifications])

@bp.route('/base_test')
def base_test():
	with current_app.open_resource('static/data/names.txt', 'r') as f:
		contents = f.read().replace('\n', ',').split(',')
	for name in contents:
		flash(name)
		program = Program(name=name, state="MO", specialty="Psychiatry")
		#Interview(date=,interviewer=program,interviewee=current_user, supplemental_required=form.supplemental_required.data, method=form.method.data)
		db.session.add(program)
		db.session.commit()
	return render_template('base_test.html', contents=contents)

def try_parsing_date(datestrings):
	d = []
	if datestrings != datestrings:
		return None
	dates = str(datestrings).replace("(full)","").replace(" ","").split(',')
	for date in dates:
		try:
			parsed = dateparser.parse(date)
			if parsed:
				if parsed.month > 6:
					parsed = parsed.replace(year=2020)
				d.append(parsed)
		except ValueError:
			pass
	return d

def create_programs(info):
	text = info.to_html()
	for row in info.itertuples():
		state = row[1]
		name = row[2]
		dates = row[3]
		if name == name and dates:
			program = Program(name=name, state=state, specialty="Psychiatry")
			interview = Interview(interviewer=program,interviewee=current_user)
			dates = list(map(lambda x: Interview_Date(date=x, interviewer=program,interviewee=current_user, invite=interview,full=False), dates))
			interview.dates = dates
			db.session.add(interview)
			db.session.commit()
		else:
			if name == name:
				program = Program(name=name, state=state, specialty="Psychiatry")
				db.session.add(program)
				db.session.commit()
	return text

@bp.route("/upload", methods=['GET', 'POST'])
@csrf.exempt
def upload_file():
	if request.method == 'POST':
		print(request.files['file'])
		f = request.files['file']
		f = pd.read_excel(f, engine='openpyxl', sheet_name='IV (Program)', header=1, usecols=[0,2,6], parse_dates=[2])
		f = f.drop(labels=[0],axis=0,inplace=False)
		f['Available Interview Dates'] = f['Available Interview Dates'].apply(lambda x: try_parsing_date(x))
		return create_programs(f)
		#return f.to_html()
	return '''
	<!doctype html>
	<title>Upload an excel file</title>
	<h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
	<form action="" method=post enctype=multipart/form-data>
	<p><input type=file name=file><input type=submit value=Upload>
	</form>
	'''

@bp.route('/analyze')
def analyze():
	with current_app.open_resource('static/data/psych2021.xlsx', encoding="utf8") as f:
		contents = f.read()
		flash(contents)
	return render_template('index.html')

@bp.route('/delete_programs')
def delete_programs():
	Program.query.delete()
	Interview.query.delete()
	Interview_Date.query.delete()
	db.session.commit()
	return render_template('programs.html')

@bp.route('/about')
def about():
	return render_template('about.html')

@bp.route('/settings')
def settings():
	return render_template('settings.html')

@bp.route('/experimental')
def experimental():
	return render_template('experimental.html')

@bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
	form = FeedbackForm()
	if form.validate_on_submit():
		send_feedback_email(form)
		flash(_('Feedback submitted!'))
		return redirect(url_for('main.feedback'))
	return render_template('feedback.html', form=form)

@bp.route('/postmethod', methods = ['POST'])
@csrf.exempt
def get_post_javascript_data():
	test_name = request.form['test_name']
	accuracy = request.form['accuracy']
	score = accuracy
	rt = request.form['rt']
	#print(jsdata, file=sys.stderr)
	#with open('somefile.txt', 'a') as the_file:
	#    the_file.write(jsdata)
	files = glob.glob('app/static/img/subitizing/*') #remove subitizing images, must change once more tests added
	for f in files:
		os.remove(f)
	test = Test(testname=test_name, score=score, reaction_time=rt, accuracy=accuracy, author=current_user)
	db.session.add(test)
	db.session.commit()
	return rt

@bp.route("/cognition", methods = ['GET'])
@login_required
def cognition():
	tests = current_user.tests.order_by(Test.timestamp.desc()).all()
	return render_template('cognition.html', tests=tests)

@bp.route("/test1", methods = ['GET'])
@login_required
def test1():
	return render_template('test1.html')

@bp.route("/subitizing", methods = ['GET'])
@login_required
def subitizing():
	return render_template('subitizing.html')

@bp.route("/unity", methods = ['GET'])
@login_required
def unity():
	return render_template('unity.html')

@bp.route("/det", methods = ['GET'])
def det():
	return render_template('det.html')

@bp.route("/slums", methods = ['GET', 'POST'])
@login_required
def slums():
	form = SLUMSForm()
	if form.validate_on_submit():
		return render_template('slums.html', form=form)
	return render_template('slums.html', form=form)

@bp.route('/delete_test/<int:test_id>')
@login_required
def delete_test(test_id):
	test = Test.query.get(test_id)
	if test.author == current_user:
		db.session.delete(test)
		db.session.commit()
	return redirect(request.referrer or url_for('cognition'))

@bp.route('/generate_images')
def generate_images():
	sequence = []
	for i in range(5):
		N = np.random.random_integers(1,9)
		x = np.random.rand(N)
		y = np.random.rand(N)
		new_dict = {}
		new_dict['index'] = str(N)

		colors = 'k'
		area = 20

		plt.scatter(x, y, s=area, c=colors)
		plt.axis([0, 1, 0, 1])
		plt.axis('scaled')

		plt.axis('off')
		loc = 'img/subitizing/{}.png'.format(np.random.random_integers(10000000,90000000))
		loc2 = 'app/static/' + loc
		new_dict['loc'] = loc
		if os.path.isfile(loc2):
			os.remove(loc2)

		plt.savefig(loc2)
		sequence.append(new_dict)
		plt.clf()
	return json.dumps(sequence)