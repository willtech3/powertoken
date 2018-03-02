"""
module ptmodels\n
Templates for user and log objects.
"""

class PtUserOld:
	def __init__(self, id, username, registered_on, goal_period, wc_login_status,
			fb_login_status, wc_daily_progress):
		self.id = id
		self.username = username
		self.registered_on = registered_on
		self.goal_period = goal_period
		self.wc_login_status = wc_login_status
		self.fb_login_status = fb_login_status
		self.wc_daily_progress = wc_daily_progress
		self.wc_weekly_progress = wc_daily_progress / 7

class PtUser:
	def __init__(self, row, wc_login_status, fb_login_status, daily_progress=0,
				weekly_progress=0):
		self.row = row
		self.wc_login_status = wc_login_status
		self.fb_login_status = fb_login_status
		self.daily_progress = daily_progress
		self.weekly_progress = weekly_progress

class PtLog:
	def __init__(self, id, user_id, timestamp, daily_progress, weekly_progress,
				fb_step_count):
		self.id = id
		self.user_id = user_id
		self.timestamp = timestamp
		self.wc_progress = wc_progress
		self.fb_step_count = fb_step_count