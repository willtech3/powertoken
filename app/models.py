"""
Contains the models to be used with the SQLAlchemy database interface.\n
Created by Abigail Franz on 3/12/2018.\n
Last modified by Abigail Franz on 4/16/2018.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

@login.user_loader
def load_admin(id):
	return Admin.query.get(int(id))

class User(db.Model):
	"""
	Represents a PowerToken user who is in recovery.
	Combines WeConnect User and Fitbit User Information
	"""
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	registered_on = db.Column(db.DateTime, index=True, default=datetime.now())
	goal_period = db.Column(db.String(16), default="daily")
	wc_id = db.Column(db.Integer, unique=True)
	wc_token = db.Column(db.String(128))
	fb_token = db.Column(db.String(256))
	logs = db.relationship("Log", backref="user", lazy="dynamic")
	activities = db.relationship("Activity", backref="user", lazy="dynamic")
	errors = db.relationship("Error", backref="user", lazy="dynamic")
	days = db.relationship("Day", backref="user", lazy="dynamic")

	def __repr__(self):
		return "<User {}>".format(self.username)


class Activity(db.Model):
	"""
	Represents a WEconnect activity.
	Links to WC_user and WC_events 
	"""
	id = db.Column(db.Integer, primary_key=True)
	wc_act_id = db.Column(db.Integer, index=True, unique=True)
	name = db.Column(db.String(256))
	expiration = db.Column(db.DateTime, index=True)
	weight = db.Column(db.Integer, default=1)
	user_id = db.Column(db.Integer, db.ForeignKey("user.wc_id"))
	events = db.relationship("Event", backref="activity", lazy="dynamic")

	def __repr__(self):
		return "<Activity '{}'>".format(self.name)


class Event(db.Model):
	"""
	Represents a WEconnect event (an activity on a particular date).
	Links to WC_activities
	"""
	id = db.Column(db.Integer, primary_key=True)
	eid = db.Column(db.String, index=True)
	start_time = db.Column(db.DateTime)	# Date portion is ignored
	completed = db.Column(db.Boolean) #Setup in polling.py for "didCheckin" == True
	day_id = db.Column(db.Integer, db.ForeignKey("day.id"))
	activity_id = db.Column(db.Integer, db.ForeignKey("activity.wc_act_id"))

	def __repr__(self):
		output = "<Event '{}' at {}>".format(self.eid, 
				self.start_time.strftime("%I:%M %p"))
		return output


class Day(db.Model):
	"""
	Represents a day of progress (which activities are completed, etc).
	Links to Powertoken User
	Links to WC_events
	"""
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, index=True)
	computed_progress = db.Column(db.Float, default=0.0)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	events = db.relationship("Event", backref="day", lazy="dynamic")

	def __repr__(self):
		return "<Day {}>".format(self.date.strftime("%Y-%m-%d"))

class Admin(UserMixin, db.Model):
	"""
	Represents a PowerToken administrator, capable of viewing the admin
	dashboard and supervising user progress.
	"""
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)		

	def __repr__(self):
		return "<Admin {}>".format(self.username)

class Log(db.Model):
	"""
	Represents a WEconnect-Fitbit progress log.
	"""
	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
	wc_progress = db.Column(db.Float)
	fb_step_count = db.Column(db.Integer)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

	def __repr__(self):
		timestr = self.timestamp.strftime("%Y-%m-%d %I:%M %p")
		return "<Log {} at {}>".format(self.user.username, timestr)

class Error(db.Model):
	"""
	Represents an error that occurred somewhere in the application(s).
	"""
	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.now())
	summary = db.Column(db.String(64))
	origin = db.Column(db.String(256))
	message = db.Column(db.String(256))
	traceback = db.Column(db.String(1048))
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

	def __repr__(self):
		return "<Error '{}', '{}'>".format(self.summary, self.message)