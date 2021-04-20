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

@bp.route('/experimental')
def experimental():
	return render_template('experimental.html')

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