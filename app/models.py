from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import json
from app import db, login
#from app.search import add_to_index, remove_from_index, query_index

followers = db.Table(
	'followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

link = db.Table(
	'link',
	db.Column('user', db.Integer, db.ForeignKey('user.id')),
	db.Column('program', db.Integer, db.ForeignKey('program.id'))
)

class User(UserMixin, db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	chats = db.relationship('Chat', backref='author', lazy='dynamic')
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	interview_impressions = db.relationship('Interview_Impression', backref='author', lazy='dynamic')
	threads = db.relationship('Thread', backref='author', lazy='dynamic')
	interviews = db.relationship('Interview', backref='interviewee', lazy='dynamic')
	interview_dates = db.relationship('Interview_Date', backref='interviewee', lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	admin = db.Column(db.Boolean())
	specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'))
	followed = db.relationship(
		'User', secondary=followers,
		primaryjoin=(followers.c.follower_id == id),
		secondaryjoin=(followers.c.followed_id == id),
		backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
	programs = db.relationship('Program', cascade="all,delete",secondary=link, back_populates='users', lazy='dynamic')
	messages_sent = db.relationship('Message',
									foreign_keys='Message.sender_id',
									backref='author', lazy='dynamic')
	messages_received = db.relationship('Message',
										foreign_keys='Message.recipient_id',
										backref='recipient', lazy='dynamic')
	last_message_read_time = db.Column(db.DateTime)
	notifications = db.relationship('Notification', backref='user',
									lazy='dynamic')
	tests = db.relationship('Test', backref='author', lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.username)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
			digest, size)

	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)

	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)

	def is_following(self, user):
		return self.followed.filter(
			followers.c.followed_id == user.id).count() > 0

	def is_following_program(self, program):
		return self.programs.filter(users.c.user_id == user.id).count() > 0

	def followed_posts(self):
		followed = Post.query.join(
			followers, (followers.c.followed_id == Post.user_id)).filter(
				followers.c.follower_id == self.id)
		own = Post.query.filter_by(user_id=self.id)
		return followed.union(own).order_by(Post.timestamp.desc())

	def get_reset_password_token(self, expires_in=600):
		return jwt.encode(
			{'reset_password': self.id, 'exp': time() + expires_in},
			current_app.config['SECRET_KEY'],
			algorithm='HS256')

	def follow_program(self, program):
		if not self.is_following_program(program):
			self.programs.append(program)

	def unfollow_program(self, program):
		if self.is_following_program(program):
			self.programs.remove(program)

	def is_following_program(self, program):
		return self.programs.filter(
			link.c.program == program.id).count() > 0

	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, current_app.config['SECRET_KEY'],
							algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)

	def new_messages(self):
		last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
		return Message.query.filter_by(recipient=self).filter(
			Message.timestamp > last_read_time).count()

	def add_notification(self, name, data):
		self.notifications.filter_by(name=name).delete()
		n = Notification(name=name, payload_json=json.dumps(data), user=self)
		db.session.add(n)
		return n


@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	language = db.Column(db.String(5))
	specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'))
	thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'))

	def __repr__(self):
		return '<Post {}>'.format(self.body)
	def get_program(self):
		return self.program or None

class Thread(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.Text)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'))
	posts = db.relationship('Post', backref='thread', lazy='dynamic')

class Interview_Impression(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
	language = db.Column(db.String(5))
	specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'))

class Program(db.Model):
	__tablename__ = 'program'
	id = db.Column(db.Integer, primary_key=True)
	specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'))
	name = db.Column(db.Text)
	body = db.Column(db.Text)
	city = db.Column(db.String(140))
	state = db.Column(db.String(140))
	accreditation_id = db.Column(db.String(140))
	status = db.Column(db.String(140))
	url = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	users = db.relationship('User', cascade="all,delete",secondary=link, back_populates='programs', lazy='dynamic')
	interviews = db.relationship('Interview', backref='interviewer', lazy='dynamic')
	interview_dates = db.relationship('Interview_Date', backref='interviewer', lazy='dynamic')
	interview_impressions = db.relationship('Interview_Impression', backref='program', lazy='dynamic')
	language = db.Column(db.String(5))
	image = db.Column(db.String(140))
	salary = db.Column(db.Text)
	salary_url = db.Column(db.Text)
	imageurl = db.Column(db.Text)
	def __repr__(self):
		return '<Program {}>'.format(self.body)
	def get_latest_interviews(self):
		return self.interviews.order_by(Interview.date.desc())[0:3]
	def get_latest_interview_dates(self):
		return self.interview_dates.order_by(Interview_Date.date.desc())[0:6]

class Message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	def get_program(self):
		return None

	def __repr__(self):
		return '<Message {}>'.format(self.body)

class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), index=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.Float, index=True, default=time)
	payload_json = db.Column(db.Text)

	def get_data(self):
		return json.loads(str(self.payload_json))

class Interview(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
	date = db.Column(db.DateTime, index=True)
	supplemental_required = db.Column(db.Boolean, default=0)
	method = db.Column(db.String(128), index=True)
	dates = db.relationship('Interview_Date', backref='invite', lazy='dynamic')
	unavailable_dates = db.Column(db.String(256), index=True)

	def __repr__(self):
		return '<Interview {}>'.format(self.program_id)

	def get_program(self):
		return Program.query.get(self.program_id)

class Interview_Date(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
	interview_id = db.Column(db.Integer, db.ForeignKey('interview.id'))
	date = db.Column(db.DateTime, index=True)
	full = db.Column(db.Boolean(), index=True)

class Test(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	testname = db.Column(db.String(140))
	score = db.Column(db.String(140))
	accuracy = db.Column(db.String(140))
	reaction_time = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	language = db.Column(db.String(5))

	def __repr__(self):
		return '<Test {}: {}>'.format(self.testname, self.score)

class Specialty(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(140), index=True)
	programs = db.relationship('Program', backref='specialty', lazy='dynamic')
	users = db.relationship('User', backref='specialty', lazy='dynamic')
	posts = db.relationship('Post', backref='specialty', lazy='dynamic')
	threads = db.relationship('Thread', backref='specialty', lazy='dynamic')
	chats = db.relationship('Chat', backref='specialty', lazy='dynamic')

class Chat(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	text = db.Column(db.Text)
	specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)