from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import json
from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from flask_seeder import Seeder, Faker, generator

class Program(SearchableMixin, db.Model):
    __tablename__ = 'program'
    __searchable__ = ['name']
    id = db.Column(db.Integer, primary_key=True)
    specialty = db.Column(db.String(140))
    name = db.Column(db.String(140))
    body = db.Column(db.String(140))
    state = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    users = db.relationship('User', secondary=link, back_populates='programs', lazy='dynamic')
    interviews = db.relationship('Interview', backref='interviewer', lazy='dynamic')
    interview_dates = db.relationship('Interview_Date', backref='interviewer', lazy='dynamic')
    posts = db.relationship('Post', backref='program', lazy='dynamic')
    language = db.Column(db.String(5))
    image = db.Column(db.String(140), default='https://images.pexels.com/photos/4386464/pexels-photo-4386464.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260')
    def __repr__(self):
        return '<Program {}>'.format(self.body)
    def get_interviews(self):
        return self.interviews.order_by(Interview.date.desc())

# SQLAlchemy database model
class User(Base):
  def __init__(self, id_num=None, name=None, age=None):
    self.id_num = id_num
    self.name = name
    self.age = age

  def __str__(self):
    return "ID=%d, Name=%s, Age=%d" % (self.id_num, self.name, self.age)

# All seeders inherit from Seeder
class DemoSeeder(Seeder):

  # run() will be called by Flask-Seeder
  def run(self):
    # Create a new Faker and tell it how to create User objects
    faker = Faker(
      cls=User,
      init={
        "id_num": generator.Sequence(),
        "name": generator.Name(),
        "age": generator.Integer(start=20, end=100)
      }
    )

    # Create 5 users
    for user in faker.create(5):
      print("Adding user: %s" % user)
      self.db.session.add(user)