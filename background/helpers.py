"""
Contains some helper functions for the background scripts.\n
Created by Abigail Franz on 3/16/2018.\n
Last modified by Abigail Franz on 5/7/2018.
"""

from datetime import datetime, time, timedelta, MAXYEAR
from db import session
from models import Activity, Day, Event, Log, User
import weconnect

TODAY = datetime.combine(datetime.now().date(), time(0, 0, 0))

def formatDate(dateStr):
	"""convert WC JSON date to date object for databse"""
	return datetime.strptime(dateStr, weconnect.DATE_FMT)

def delete_all_content():
	session.query(Log).delete()
	session.query(Event).delete()
	session.query(Activity).delete()
	session.query(Day).delete()
	session.query(User).delete()
	
	try:
		session.commit()
	except:
		session.rollback()
	

def remove_incomplete_users():
	"""
	Go through the users table of the database and check 2 things:
	1. All user fields are complete, and incomplete profiles are removed.
	2. All WEconnect and Fitbit access tokens are unexpired.
	Remove all users who do not meet these criteria, and any other records that
	belong to the deleted users.
	"""
	""" #1 """
	users = session.query(User).all()
	for user in users:
		
		if not all([user.username, user.wc_id, user.wc_token, user.fb_token]):
			activities = user.activities.all()
			for activity in activities:
				session.delete(activity)
			days = user.days.all()
			for day in days:
				events = day.events.all()
				for event in events:
					session.delete(event)
				session.delete(day)
			session.delete(user)
	session.commit()


# Make sure no activities are expired
def remove_expired_activities():
	"""
	Remove all activities whose expiration date is in the past from the
	database.

	As of 5/7/2018, we're no longer doing this. It causes a lot of problems
	with the Events table. Having expired activities sitting in the database
	should be all right.
	"""
	activities = session.query(Activity).all()
	now = datetime.now()
	for act in activities:
		if act.expiration <= now:
			session.delete(act)
	session.commit()

def add_or_update_activity(activity, user):
	"""
	Insert new activity row into the database if it doesn't already exist and
	is not expired. If it exists but has been updated, update it in the
	database. Return "Inserted" if activity was inserted, "Updated" if updated,
	and False if neither.

	:param dict activity: an activity from WEconnect in JSON format\n
	:param background.models.User user: the user to which the activity belongs
	"""
	# Determines the start and end times and expiration date (if any)
	st, et, expiration = extract_params(activity)
	act_id = activity["activityId"]

	# Flag indicating whether or not the activity was inserted/updated
	status = False

	# If the activity already exists in the database, sees if it's been
	# modified recently. If yes, updates it. If not, ignores it.
	existing = session.query(Activity).filter(Activity.wc_act_id == act_id).first()
	if existing:
		modified = datetime.strptime(activity["dateModified"], weconnect.DATE_FMT)
		if modified >= datetime.now() - timedelta(days=1):
			existing.name = activity["name"]
			existing.expiration = expiration
			session.commit()
			status = "Updated"
		else:
			status = False
	else:
		# If the activity doesn't exist in the database, adds it.
		new = Activity(wc_act_id=act_id, name=activity["name"], 
			expiration=expiration, user=user)
		session.add(new)
		session.commit()
		status = "Inserted"

	return status

def extract_params(activity):
	"""
	Given a JSON activity object from WEconnect, extract the important
	parameters (start time, end time, and expiration date).

	:param dict activity: an activity from WEconnect in JSON format
	"""
	# Determines the start and end times
	ts = datetime.strptime(activity["dateStart"], weconnect.DATE_FMT)
	te = ts + timedelta(minutes=activity["duration"])

	# Determines the expiration date (if any)
	expiration = datetime(MAXYEAR, 12, 31)
	if activity["repeat"] == "never":
		expiration = te
	if activity["repeatEnd"] != None:
		expiration = datetime.strptime(activity["repeatEnd"], weconnect.DATE_FMT)

	return ts, te, expiration

def get_users_with_current_events():
	"""
	Get a list of all the users who have events starting or ending within
	the next 15 minutes. Not currently in use.
	"""
	users_to_monitor = []
	now = datetime.now().time()
	margin = timedelta(minutes=15)
	users = session.query(User).all()
	for user in users:
		day = user.days.filter(Day.date == TODAY)
		events = day.events.filter((Event.start_time - margin).time() <= now).\
				filter(now <= (Event.end_time + margin).time()).count()
		if events:
			users_to_monitor.append(user)
	return users_to_monitor

def get_yesterdays_progress(user):
	"""
	Get the daily_progress component from yesterday's last log. Not currently
	in use.

	:param background.models.User user: the user for which to get progress
	"""
	yesterdays_logs = []
	yesterday = datetime.now() - timedelta(days=1)
	start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0)
	end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59)
	yest_log = user.logs.filter(Log.timestamp > start, Log.timestamp < end).\
			order_by(Log.timestamp.desc()).first()
	return yest_log.daily_progress

def update_activities(user):
	"""
	If the user has added or updated any WEconnect activities, update the
	database.

	:param background.models.User user
	"""
	wc_acts = weconnect.get_activities(user)
	for act in wc_acts:
		add_or_update_activity(act, user)

def populate_today(user):
	"""
	Populate the database (`day` and `event` tables) with a list of the user's 
	events that occur today.

	:param background.models.User user: the user for which to get events
	"""
	# Add a new Day to the user's days table if it doesn't already exist
	day = user.days.filter(Day.date == TODAY).first()
	if day is None:
		day = Day(date=datetime(TODAY.year, TODAY.month, TODAY.day), user=user)
		session.add(day)
		session.commit()

	# Get today's events from WEconnect and add them to the day's events table
	activity_events = weconnect.get_todays_events(user)
	for wc_act in activity_events:
		act = user.activities.filter(Activity.wc_act_id == wc_act["activityId"]).first()
		for wc_ev in wc_act["events"]:
			# If the event doesn't already exist for today, add it
			event = session.query(Event).filter(Event.eid == wc_ev["eid"]).first()
			if event:
				modified = datetime.strptime(wc_act["dateModified"], weconnect.DATE_FMT)
				if modified >= datetime.now() - timedelta(days=1):
					event.start_time = datetime.strptime(wc_ev["dateStart"], weconnect.DATE_FMT)
					event.end_time = act.start_time + timedelta(minutes=wc_ev["duration"])
					event.completed = wc_ev["didCheckin"]
			else:
				st = datetime.strptime(wc_ev["dateStart"], weconnect.DATE_FMT)
				et = st + timedelta(minutes=wc_ev["duration"])
				event = Event(eid=wc_ev["eid"], start_time=st, end_time=et,
						completed=wc_ev["didCheckin"], day=day, activity=act)
				session.add(event)
	session.commit()

def compute_possible_score(day):
    """
	Compute the highest possible score for a particular user on a particular
	day.

	:param background.models.Day day
	"""
    events = day.events.all()
    score = 0
    for ev in events:
        score += ev.activity.weight
    return score

def compute_days_progress(day):
	""" FADE VERSION
	Compute the user's actual progress (decimal) on a particular day. The
	algorithm essentially allows progress from activities with weights of 5 to
	persist for 5 days, 4 for 4 days, etc. If the final percentage is more than
	100%, the extra is truncated.

	:param background.models.Day day
	"""
	score = 0
	day_0_acts = day.events.filter(Event.completed).all()
	for act in day_0_acts:
		score += act.activity.weight

	day_1_ago = day.user.days.filter_by(date=(day.date - timedelta(1))).first()
	if not day_1_ago is None:
		day_1_acts = day_1_ago.events.filter(Event.completed).all()
		for act in day_1_acts:
			score += (act.activity.weight - 1)

	day_2_ago = day.user.days.filter_by(date=(day.date - timedelta(2))).first()
	if not day_2_ago is None:
		day_2_acts = day_2_ago.events.filter(Event.completed).all()
		for act in day_2_acts:
			score += (act.activity.weight - 2) if act.activity.weight > 1 else 0

	day_3_ago = day.user.days.filter_by(date=(day.date - timedelta(3))).first()
	if not day_3_ago is None:
		day_3_acts = day_3_ago.events.filter(Event.completed).all()
		for act in day_3_acts:
			score += (act.activity.weight - 3) if act.activity.weight > 2 else 0

	day_4_ago = day.user.days.filter_by(date=(day.date - timedelta(4))).first()
	if not day_4_ago is None:
		day_4_acts = day_4_ago.events.filter(Event.completed).all()
		for act in day_4_acts:
			score += (act.activity.weight - 4) if act.activity.weight > 3 else 0

	possible_score = compute_possible_score(day)
	computed_score = float(score) / float(possible_score) if score < possible_score else 1.0
	return float(score) / float(possible_score)
	
def compute_days_progress_tally(day):
	''' TALLY
	Get current progress, compare with possible progress for that day.
	Return a percentage of progress completed for display on fitbit
	'''
	
	total_activities = day.events.all() #BUG HERE: list object has no attribte events
	complete_activities = day.events.filter(Event.complete).all() #BUG HERE: Event has no attribute complete
	current_score = float(len(complete_activities) / len(total_activities))
	return float(current_score)
		



	