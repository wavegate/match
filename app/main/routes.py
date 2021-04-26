from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
	jsonify, current_app, Response, stream_with_context, make_response, session
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db, csrf, socketio
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm, ProgramForm, AddInterviewForm, FeedbackForm, SLUMSForm, CreateSpecialtyForm, SpecialtyForm, ThreadForm
from app.models import User, Post, Program, Message, Notification, Interview, Interview_Date, Test, Specialty, Thread, Interview_Impression, Chat
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
import time
import ast
from flask_socketio import join_room, leave_room, emit

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
	return render_template('landing.html', specialties = Specialty.query.order_by(Specialty.name))

@bp.route('/programs/<specialty>', methods=['GET', 'POST'])
def programs(specialty):
	form = ProgramForm()
	if form.validate_on_submit() and current_user.admin:
		program = Program(name=form.name.data, specialty=form.specialty.data, body=form.body.data, image=form.image.data, state=form.state.data)
		db.session.add(program)
		db.session.commit()
		flash(_('Program added!'))
		return redirect(url_for('main.programs'))
	programs = Program.query.filter_by(specialty=specialty).order_by(Program.timestamp.desc())
	return render_template('programs.html', title=_('Programs'),
						   programs=programs, form=form, specialty=specialty)

@bp.route('/program/<program_id>', methods=['GET','POST'])
def program(program_id):
	specialty2 = session.get('specialty')
	program = Program.query.filter_by(id=program_id).first_or_404()
	interviews = program.interviews.order_by(Interview.date.desc())
	page = request.args.get('page', 1, type=int)
	postform = PostForm()
	if postform.validate_on_submit() and current_user.is_authenticated:
		interview_impression = Interview_Impression(body=postform.post.data, author=current_user, program=program)
		db.session.add(interview_impression)
		db.session.commit()
		flash(_('Your interview impression is now live!'))
		return redirect(url_for('main.program', program_id=program_id))
	interview_impressions = program.interview_impressions.order_by(Interview_Impression.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.program', id=program_id,
					   page=interview_impressions.next_num) if interview_impressions.has_next else None
	prev_url = url_for('main.program', id=program_id,
					   page=interview_impressions.prev_num) if interview_impressions.has_prev else None
	form = EmptyForm()
	return render_template('program.html', specialty2=specialty2,next_url=next_url, prev_url=prev_url,program=program, interviews=program.interviews, postform=postform, form=form, interview_impressions=interview_impressions.items)

@bp.route('/delete_program/<int:program_id>', methods=['POST'])
@login_required
def delete_program(program_id):
	if current_user.admin:
		program = Program.query.get(program_id)
		specialty = program.specialty
		db.session.delete(program)
		db.session.commit()
	return redirect(request.referrer)

@bp.route('/delete_post/<int:post_id>', methods=['GET','POST'])
@login_required
def delete_post(post_id):
	post = Post.query.get(post_id)
	if current_user == post.author:
		db.session.delete(post)
		db.session.commit()
		flash('Post deleted!')
	return redirect(request.referrer)

@bp.route('/delete_interview_impression/<int:interview_impression_id>', methods=['GET','POST'])
@login_required
def delete_interview_impression(interview_impression_id):
	interview_impression = Interview_Impression.query.get(interview_impression_id)
	if current_user == interview_impression.author:
		db.session.delete(interview_impression)
		db.session.commit()
		flash('Interview impression deleted!')
	return redirect(request.referrer)

@bp.route('/add_interview/<int:program_id>', methods=['GET', 'POST'])
@login_required
def add_interview(program_id):
	specialty2 = session.get('specialty')
	program = Program.query.filter_by(id=program_id).first_or_404()
	form = AddInterviewForm(current_user.username, program)
	if form.validate_on_submit():
		interview = Interview(date=form.date.data,interviewer=program,interviewee=current_user, supplemental_required=form.supplemental_required.data, method=form.method.data)
		dates = None
		dates2 = None
		if request.form['interview_dates'] != '':
			try:
				available_dates = list(map(lambda x:datetime.strptime(x, '%m/%d/%Y'), request.form['interview_dates'].split(',')))
				dates = list(map(lambda x: Interview_Date(date=x, interviewer=program,interviewee=current_user, invite=interview,full=False), available_dates))
			except ValueError:
				pass
		if request.form['interview_invites'] != '':
			try:
				unavailable_dates = list(map(lambda x:datetime.strptime(x, '%m/%d/%Y'), request.form['interview_invites'].split(',')))
				dates2 = list(map(lambda x: Interview_Date(date=x, interviewer=program,interviewee=current_user, invite=interview,full=True), unavailable_dates))
			except ValueError:
				pass
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
		return redirect(url_for('main.program', program_id=program.id))
	return render_template('add_interview.html',specialty2=specialty2, title=_('Add Interview Offer'),
						   form=form, program=program)

@bp.route('/delete_interview/<int:interview_id>', methods=['POST'])
@login_required
def delete_interview(interview_id):
	interview = Interview.query.get(interview_id)
	if current_user == interview.interviewee:
		program = interview.interviewer
		db.session.delete(interview)
		db.session.commit()
		flash('Interview deleted!')
	return redirect(request.referrer)

@bp.route('/user/<username>', methods=['GET','POST'])
@login_required
def user(username):
	specialty2 = session.get('specialty')
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	posts = user.posts.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.user', username=user.username,
					   page=posts.next_num) if posts.has_next else None
	prev_url = url_for('main.user', username=user.username,
					   page=posts.prev_num) if posts.has_prev else None
	form = EditProfileForm(current_user.username)
	if form.validate_on_submit() and current_user == user:
		current_user.username = form.username.data
		current_user.about_me = form.about_me.data
		db.session.commit()
		flash(_('Your changes have been saved.'))
		return render_template('user.html', user=user, interviews=user.interviews,posts=posts.items,next_url=next_url,prev_url=prev_url,form=form)
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.about_me.data = current_user.about_me
	return render_template('user.html', specialty2=specialty2, user=user, interviews=user.interviews,posts=posts.items, programs=user.programs,
						   next_url=next_url, prev_url=prev_url, form=form)

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

@bp.route('/follow_program/<int:program_id>', methods=['POST'])
@login_required
def follow_program(program_id):
	form = EmptyForm()
	if form.validate_on_submit():
		program = Program.query.filter_by(id=program_id).first()
		if program is None:
			flash(_('Program not found.'))
			return redirect(url_for('main.programs'))
		current_user.follow_program(program)
		db.session.commit()
		flash(_('You are following %(name)s!', name=program.name))
		return redirect(url_for('main.specialty', id=program.specialty_id))
	else:
		return redirect(url_for('main.specialty', id=program.specialty_id))

@bp.route('/unfollow_program/<int:program_id>', methods=['POST'])
@login_required
def unfollow_program(program_id):
	form = EmptyForm()
	if form.validate_on_submit():
		program = Program.query.filter_by(id=program_id).first()
		if program is None:
			flash(_('Program not found.'))
			return redirect(url_for('main.programs'))
		current_user.unfollow_program(program)
		db.session.commit()
		flash(_('You are not following %(name)s.', name=program.name))
	return redirect(url_for('main.specialty', id=program.specialty_id))

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
	specialty2 = session.get('specialty')
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
	return render_template('send_message.html', specialty2=specialty2, title=_('Send Message'),
						   form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
	specialty2 = session.get('specialty')
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
	return render_template('messages.html', specialty2=specialty2, messages=messages.items,
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

@bp.route("/upload/<specialty>", methods=['GET', 'POST'])
@csrf.exempt
def upload_file(specialty):
	if request.method == 'POST':
		def generate():
			spec = Specialty.query.filter_by(name=specialty).first_or_404()
			f = request.files['file']
			f = pd.read_excel(f, engine='openpyxl', sheet_name=specialty, header=0, usecols=[0,1,2])
			for index, row in f.iterrows():
				state = row[0]
				name = row[1]
				dates = ast.literal_eval(row[2])
				d = []
				for date in dates:
					d.append(dt.datetime.strptime(date, '%m/%d/%Y'))
				program = Program(name=name, state=state, specialty=spec)
				interview = Interview(interviewer=program,interviewee=current_user)
				dates = list(map(lambda x: Interview_Date(date=x, interviewer=program,interviewee=current_user, invite=interview,full=False), d))
				interview.dates = dates
				db.session.add(interview)
				db.session.commit()
				yield(str(index))
		return Response(stream_with_context(generate()))
	return render_template('upload.html')

@bp.route('/delete_programs')
def delete_programs():
	if current_user.admin:
		Program.query.delete()
		Interview.query.delete()
		Interview_Date.query.delete()
		db.session.commit()
	return redirect(request.referrer)

@bp.route('/about', methods=['GET','POST'])
def about():
	specialty2 = session.get('specialty')
	form = FeedbackForm()
	if form.validate_on_submit():
		send_feedback_email(form)
		flash(_('Feedback submitted!'))
		return redirect(url_for('main.about'))
	return render_template('about.html', specialty2=specialty2, form=form)

@bp.route('/settings')
def settings():
	specialty2 = session.get('specialty')
	return render_template('settings.html', specialty2=specialty2)

@bp.route('/specialty/<int:id>', methods=['GET', 'POST'])
def specialty(id):
	session['specialty'] = str(id)
	specialty2 = session.get('specialty')
	form = ProgramForm()
	specialty = Specialty.query.get(id)
	current_user.specialty_id = id
	db.session.commit()
	if form.validate_on_submit() and current_user.admin:
		program = Program(name=form.name.data, specialty=specialty, state=form.state.data)
		db.session.add(program)
		db.session.commit()
		flash(_('Program added!'))
		return redirect(url_for('main.specialty', id=specialty.id))
	return render_template('specialty.html', specialty2=specialty2, specialty=specialty, title=specialty.name, programs=specialty.programs.order_by(Program.timestamp.desc()), form=form)

@bp.route('/create_specialty', methods=['GET','POST'])
@login_required
def create_specialty():
	if current_user.admin:
		specialty2 = session.get('specialty')
		form = CreateSpecialtyForm()
		if form.validate_on_submit():
			specialty = Specialty(name=form.name.data)
			db.session.add(specialty)
			db.session.commit()
			flash(_('Specialty Created!'))
			return redirect(url_for('main.index'))
		return render_template('create_specialty.html', form=form, specialty2=specialty2)
	else:
		return redirect(request.referrer)

@bp.route('/delete_specialty/<int:id>', methods=['GET','POST'])
@login_required
def delete_specialty(id):
	if current_user.admin:
		specialty = Specialty.query.get(id)
		db.session.delete(specialty)
		db.session.commit()
	return redirect(request.referrer)

@bp.route('/chat/<int:id>', methods=['GET', 'POST'])
@csrf.exempt
def chat(id):
	specialty2 = session.get('specialty')
	specialty = Specialty.query.get(id)
	session['room'] = str(specialty.id)
	chats = Chat.query.filter_by(specialty=specialty).order_by(Chat.timestamp.asc())[0:25]
	if current_user.is_authenticated:
		name = current_user.username
	else:
		name = 'anonymous'
	room = specialty.name
	if name == '' or room == '':
		return redirect(request.referrer)
	return render_template('chat.html', name=name, room=room, specialty=specialty, specialty2=specialty2, chats=chats)

@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    specialty=Specialty.query.get(room)
    #if current_user.is_authenticated:
    #	emit('status', {'msg': current_user.username + ' has entered the room.'}, room=room)
    #	chat = Chat(author=current_user, text=current_user.username + ' has entered the room.', specialty=specialty)
    #else:
    #	emit('status', {'msg': 'anonymous has entered the room.'}, room=room)
    #	chat = Chat(text='anonymous has entered the room.', specialty=specialty)
    #db.session.add(chat)
    #if Chat.query.count() > 25:
    #	oldest_chat = Chat.query.order_by(Chat.timestamp.asc())[0]
    #	db.session.delete(oldest_chat)
    #db.session.commit()

@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    specialty=Specialty.query.get(room)
    if current_user.is_authenticated:
    	emit('message', {'msg': current_user.username + ': ' + message['msg']}, room=room)
    	chat = Chat(author=current_user, text=current_user.username + ':' + message['msg'], specialty=specialty)
    else:
    	emit('message', {'msg': 'anonymous'+ ': ' + message['msg']}, room=room)
    	chat = Chat(text='anonymous'+ ':' + message['msg'], specialty=specialty)
    db.session.add(chat)
    if Chat.query.count() > 25:
    	oldest_chat = Chat.query.order_by(Chat.timestamp.asc())[0]
    	db.session.delete(oldest_chat)
    db.session.commit()

@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    specialty=Specialty.query.get(room)
    if current_user.is_authenticated:
    	emit('status', {'msg': current_user.username + ' has left the room.'}, room=room)
    	chat = Chat(author=current_user, text=current_user.username + ' has left the room.', specialty=specialty)
    else:
    	emit('status', {'msg': 'anonymous has left the room.'}, room=room)
    	chat = Chat(text='anonymous has left the room.', specialty=specialty)
    db.session.add(chat)
    if Chat.query.count() > 25:
    	oldest_chat = Chat.query.order_by(Chat.timestamp.asc())[0]
    	db.session.delete(oldest_chat)
    db.session.commit()

@bp.route('/forum/<int:specialty_id>', methods=['GET', 'POST'])
def threads(specialty_id):
	specialty2 = session.get('specialty')
	page = request.args.get('page', 1, type=int)
	specialty = Specialty.query.get(specialty_id)
	threads = specialty.threads.order_by(Thread.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.specialty', specialty_id=specialty_id,
					   page=threads.next_num) if threads.has_next else None
	prev_url = url_for('main.specialty', specialty_id=specialty_id,
					   page=threads.prev_num) if threads.has_prev else None
	return render_template('threads.html', specialty2 = specialty2, next_url=next_url, prev_url=prev_url, specialty=specialty, threads=threads.items)

@bp.route('/new_thread/<int:specialty_id>', methods=['GET', 'POST'])
def new_thread(specialty_id):
	specialty2 = session.get('specialty')
	threadform = ThreadForm()
	specialty = Specialty.query.get(specialty_id)
	if threadform.validate_on_submit():
		thread = Thread(body=threadform.body.data, author=current_user,title=threadform.title.data,
					specialty=Specialty.query.get(specialty_id))
		db.session.add(thread)
		db.session.commit()
		flash(_('Your thread is now live!'))
		return redirect(url_for('main.threads', specialty_id=specialty_id))
	return render_template('new_thread.html', specialty2 = specialty2, specialty=specialty, threadform=threadform)

@bp.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
	specialty2 = session.get('specialty')
	page = request.args.get('page', 1, type=int)
	postform = PostForm()
	thread = Thread.query.get(thread_id)
	if postform.validate_on_submit():
		post = Post(body=postform.post.data, author=current_user, thread_id=thread_id)
		db.session.add(post)
		db.session.commit()
		flash(_('Your post is now live!'))
		return redirect(url_for('main.thread', thread_id=thread_id))
	posts = thread.posts.order_by(Post.timestamp.desc()).paginate(
		page, current_app.config['POSTS_PER_PAGE'], False)
	next_url = url_for('main.thread', thread_id=thread_id,
					   page=posts.next_num) if posts.has_next else None
	prev_url = url_for('main.thread', thread_id=thread_id,
					   page=posts.prev_num) if posts.has_prev else None
	return render_template('thread.html', specialty2 = specialty2, next_url=next_url, prev_url=prev_url, postform=postform, posts=posts.items, thread=thread)

@bp.route('/delete_thread/<int:thread_id>', methods=['GET','POST'])
@login_required
def delete_thread(thread_id):
	thread = Thread.query.get(thread_id)
	if current_user == thread.author:
		db.session.delete(thread)
		db.session.commit()
		flash('Thread deleted!')
	return redirect(request.referrer)

@bp.route('/seedspecialties')
def seedspecialties():
	if current_user.admin:
		specialties = ['Anesthesiology', 'Child Neurology', 'Dermatology', 'Diagnostic Radiology', 'Emergency Medicine', 'Family Medicine', 'Internal Medicine', 'Interventional Radiology', 'Neurological Surgery', 'Neurology', 'Obstetrics and Gynecology', 'Orthopaedic Surgery', 'Otolaryngology', 'Pathology', 'Pediatrics', 'Physical Medicine and Rehabilitation', 'Plastic Surgery', 'Psychiatry', 'Radiation Oncology', 'General Surgery', 'Thoracic Surgery', 'Urology', 'Vascular Surgery', 'Prelim or Transitional Year']
		for specialty in specialties:
			db.session.add(Specialty(name=specialty))
			db.session.commit()
	return redirect(url_for('main.index'))

@bp.route('/start', methods=['POST'])
def get_counts():
	data = json.loads(request.data.decode())
	url = data["url"]
