"""
Handles routing and form processing for the PowerToken Flask app.\n
Created by Jasmine Jones\n
Last modified by Abigail Franz on 3/15/2018
"""

from datetime import datetime
from flask import flash, redirect, render_template, request, url_for
from flask_login import (
	current_user, login_user, logout_user, login_required
)
from werkzeug.urls import url_parse
from app import app, db
from app.forms import (
	AdminLoginForm, AdminRegistrationForm, UserLoginForm, UserWcLoginForm
)
from app.models import Admin, User, Log, Activity
from app.apis import login_to_wc, complete_fb_login
from app.viewmodels import UserViewModel, LogViewModel

@app.route("/")
@app.route("/index")
@app.route("/home")
def user_home():
	username = request.args.get("username")

	# If the user isn't logged in, redirect to the PowerToken login.
	if username is None:
		print("Redirecting to login.")
		return redirect(url_for("user_login"))

	# If the user is logged in, show the welcome page.
	else:
		print("Showing the homepage.")
		return render_template("user_home.html", username=username)

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
	form = UserLoginForm()

	# POST: processes the PowerToken login form
	if form.is_submitted():
		print("user_login form submitted.")
		if not form.validate():
			print("user_login form did not validate.")
			print(form.errors)
		else:
			print("user_login form validated.")
		username = form.username.data
		user = User.query.filter_by(username=username).first()

		# If the user has not been added to the database, add the user to the
		# database and redirect to the WEconnect login.
		if user is None:
			print("User {} isn't in the db yet. Adding to db".format(username))
			user = User(username=username)
			db.session.add(user)
			db.session.commit()
			print("Redirecting to WC login.")
			return redirect(url_for("user_wc_login", username=username))
			
		# If the user exists in the database, but the WEconnect (or Fitbit)
		# info isn't filled out, redirect to the WEconnect login.
		if any([not user.wc_id, not user.wc_token, not user.fb_token]):# user.wc_id is None or user.wc_token is None or user.fb_token is None:
			print("Not all the info is filled out for {}. Redirecting to WC login.".format(user))
			return redirect(url_for("user_wc_login", username=username))

		if user.wc_id and user.wc_token and not user.fb_token:
			return redirect(url_for("user_fb_login", username=username))
			
		# If the user exists in the database, and the WEconnect and Fitbit info
		# is already filled out, bypass the login process.
		print("All info is filled out for {}. Redirecting to home.".format(user))
		return redirect(url_for("user_home", username=username))

	# GET: Render the PowerToken login page.
	print("Received GET request for user_login page.")
	error = request.args.get("error")
	if error:
		return render_template("user_login.html", form=form, error=error)
	else:
		return render_template("user_login.html", form=form)

@app.route("/user_wc_login", methods=["GET", "POST"])
def user_wc_login():
	form = UserWcLoginForm()

	# POST: Process the WEconnect login form.
	if form.is_submitted():
		print("wc_login form submitted.")

		if not form.validate():
			print("wc_login form did not validate.")
			print(form.errors)
		else:
			print("wc_login form validated.")

		username = request.args.get("username")

		# If the username wasn't saved, return to the original PowerToken login
		# page.
		if username is None:
			print("username is None.")
			return redirect(url_for("user_login", error="Invalid username"))

		# Get the user with that username from the database.
		user = User.query.filter_by(username=username).first()

		# If the user with that username isn't in the database for whatever
		# reason, go back to the PowerToken login page.
		if user is None:
			print("User with username {} doesn't exist. Redirecting to user_login.".format(username))
			return redirect(url_for("user_login", error="Invalid user"))

		# If everything is okay so far, get WEconnect info from the form and
		# login to external WEconnect server.
		email = form.email.data
		password = form.password.data
		successful_result = login_to_wc(email, password)

		# If the username or password is incorrect, prompt the user to re-enter
		# credentials.
		if not successful_result:
			print("Incorrect WC email or password. Reloading wc_login page.")
			errors = ["Incorrect email or password"]
			return render_template("user_wc_login.html", form=form, errors=errors)

		# If the login was successful, store the WEconnect ID and access token
		# in the database, and redirect to the Fitbit login.
		user.wc_id = successful_result[0]
		user.wc_token = successful_result[1]
		print("Updating {} with wc_id = {} and wc_token = {}".format(user, user.wc_id, user.wc_token))
		db.session.commit()
		print("Redirecting to fb_login.")
		return redirect(url_for("user_fb_login", username=username))

	# GET: Render the WEconnect login page.
	print("Received GET request for wc_login page.")
	return render_template("user_wc_login.html", form=form)

@app.route("/user_fb_login", methods=["GET", "POST"])
def user_fb_login():
	# POST: Process response from external Fitbit server.
	if request.method == "POST":
		print("External fb_login POST data received.")

		# Extract the Fitbit token and username from the response data.
		fb_token, username = complete_fb_login(request.data)

		# If the username wasn't saved, return to the original PowerToken login
		# page.
		if username is None:
			print("username is None. Redirecting to user_login.")
			return redirect(url_for("user_login", error="Invalid username"))

		# Get the user with that username from the database.
		user = User.query.filter_by(username=username).first()

		# If the user with that username isn't in the database for whatever
		# reason, go back to the PowerToken login page.
		if user is None:
			print("User with username {} doesn't exist. Redirecting to user_login.".format(username))
			return redirect(url_for("user_login", error="Invalid user"))
		
		# If everything is okay so far, add the Fitbit token to the database.
		user.fb_token = fb_token
		print("Updating {} with fb_token = {}".format(user, user.fb_token))
		db.session.commit()

		# This code will never be called but must be present
		return render_template("user_home.html", username=username)

	# GET: Render Fitbit page, which redirects to external login.
	elif request.method == "GET":
		print("Received GET request for fb_login page.")
		username = request.args.get("username")
		return render_template("user_fb_login.html", username=username)

@app.route("/admin")
@app.route("/admin/")
@app.route("/admin/index")
@app.route("/admin/home")
@login_required
def admin_home():
	users = User.query.order_by(User.registered_on).all()
	user_vms = [UserViewModel(user) for user in users]
	return render_template("admin_home.html", user_vms=user_vms)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
	print("Called admin_login()")
	if current_user.is_authenticated:
		return redirect(url_for("admin_home"))
	form = AdminLoginForm()

	# POST: If a valid form was submitted
	if form.validate_on_submit():
		print("Submitted AdminLoginForm")
		admin = Admin.query.filter_by(username=form.username.data).first()
		if admin is None or not admin.check_password(form.password.data):
			flash("Invalid username or password")
			print("Invalid username or password")
			return redirect(url_for("admin_login"))
		login_user(admin, remember=form.remember_me.data)
		next_page = request.args.get("next")
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for("admin_home")
		print("next_page = {}".format(str(next_page)))
		return redirect(next_page)

	# GET: Renders the admin login template
	return render_template("admin_login.html", form=form)

@app.route("/admin/logout")
def admin_logout():
	logout_user()
	return redirect(url_for("admin_home"))

@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
	if current_user.is_authenticated:
		return redirect(url_for("admin_home"))
	form = AdminRegistrationForm()
	if form.validate_on_submit():
		admin = Admin(username=form.username.data, email=form.email.data)
		admin.set_password(form.password.data)
		db.session.add(admin)
		db.session.commit()
		login_user(admin, remember=False)
		return redirect(url_for("admin_home"))
	return render_template("admin_register.html", form=form)

@app.route("/admin/progress_logs")
@login_required
def admin_progress_logs():
	logs = Log.query.all()
	log_vms = [LogViewModel(log) for log in logs]
	return render_template("admin_progress_logs.html", log_vms=log_vms)

@app.route("/admin/user_stats")
@login_required
def admin_user_stats():
	users = User.query.order_by(User.registered_on).all()
	user_vms = [UserViewModel(user) for user in users]
	return render_template("admin_user_stats.html", user_vms=user_vms)

@app.route("/admin/system_logs")
@login_required
def admin_system_logs():
	return render_template("admin_system_logs.html")