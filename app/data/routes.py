from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
	jsonify, current_app, Response, stream_with_context, make_response, session
from flask_login import current_user, login_required
from app import db, csrf
from app.models import User, Post, Program, Message, Notification, Interview, Interview_Date, Test, Specialty, Chat
import logging
import re
import pandas as pd
import datetime as dt
import dateutil.parser
import os
import json
from app.data import bp
import urllib.request
import app

@bp.route('/delete_specialties')
def delete_specialties():
	if current_user.admin:
		Specialty.query.delete()
		db.session.commit()
	return redirect(url_for('main.index'))

@bp.route('/create_specialties')
def create_specialties():
	if current_user.admin:
		with current_app.open_resource('static/data/specialty.json') as f:
			data = json.load(f)
			for i in data:
				db.session.add(Specialty(name=i['specialty'][0]))
				db.session.commit()
		return str(data)
	return redirect(url_for('main.index'))

@bp.route('/delete_programs')
def delete_programs():
	if current_user.admin:
		Program.query.delete()
		db.session.commit()
	return redirect(url_for('main.index'))

@bp.route('/create_programs')
def create_programs():
	def generate(): 
		if current_user.admin:
			with current_app.open_resource('static/data/programs.json') as f:
				data = json.load(f)
				count = 0
				for i in data:
					specialty = Specialty.query.filter_by(name=i['specialty']).first_or_404()
					db.session.add(Program(specialty=specialty, name=next(iter(i['program']), None), city=next(iter(i['city']), None), state=next(iter(i['state']), None), accreditation_id=next(iter(i['accreditation_id']), None),status=next(iter(i['status']), None),url=next(iter(i['url']), None)))
					db.session.commit()
					count = count + 1
					yield(str(count) + " ")
	return Response(stream_with_context(generate()))

@bp.route('/delete_interviews')
def delete_interviews():
	if current_user.admin:
		Interview.query.delete()
		db.session.commit()
	return redirect(url_for('main.index'))

@bp.route('/delete_interview_dates')
def delete_interview_dates():
	if current_user.admin:
		Interview_Date.query.delete()
		db.session.commit()
	return redirect(url_for('main.index'))

@bp.route('/delete_chats')
def delete_chats():
	if current_user.admin:
		Chat.query.delete()
		db.session.commit()
	return redirect(url_for('main.index'))

@bp.route('/remove_user_specialties')
def remove_user_specialties():
	if current_user.admin:
		users = User.query.all()
		for user in users:
			user.specialty_id = None
			user.programs = []
		db.session.commit()
		specialties = Specialty.query.all()
		for specialty in specialties:
			specialty.users = []
			specialty.programs = []
		db.session.commit()
		for program in Program.query.all():
			program.users = []
		db.session.commit()
	return redirect(url_for('main.index'))