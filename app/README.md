# PowerToken Flask App 
### (Last Update, 3/25/2018)


## Dependencies:

* Python 2.7 (but should be compatible with Python 3)
* Flask 0.12.2 (http://flask.pocoo.org/)
* Flask-Login 0.4.1 (https://flask-login.readthedocs.io/en/latest/)
* Flask-SQLAlchemy 2.3.2 (http://flask-sqlalchemy.pocoo.org/2.3/)
* Flask-Migrate 2.1.1 (https://flask-migrate.readthedocs.io/en/latest/)
* Flask-WTF 0.14.2 (https://flask-wtf.readthedocs.io/en/stable/)
* Python Requests 2.18.4 (http://docs.python-requests.org/en/master/)
* Gunicorn 19.7.1 (http://docs.gunicorn.org/en/stable/index.html)
* JavaScript Fetch API (https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
* Fitbit Web API (https://dev.fitbit.com/reference/web-api/quickstart/)
* WEconnect Web API (documentation not available to the public)


## Client Side (User):

The user navigates to the URL on which the application is hosted (currently https://powertoken.grouplens.org/). If he is not logged in, he will be redirected to the login page. He enters the username we gave him into the form field and clicks "NEXT". If he has already signed up with PowerToken, he is redirected to the homepage and is good to go.

If the user has never logged into PowerToken before, she is redirected to the WEconnect login page and must enter her WEconnect credentials. These credentials are not seen or saved by the researchers. Upon clicking next, she is redirected to the external Fitbit login page, where she must grant the application permission to access her data. Then she is sent back to the homepage.

Back on the homepage, the user will see a welcome message. He is good to go!


## Client Side (Admin):

If the client appends "/admin" to the URL (https://powertoken.grouplens.org/admin), she is redirected to the administrator portion of the application. This area is protected by an authentication process.


## Server Side:

One way to start the Flask server is to run `python powertoken.py` from the parent directory. The server will serve all webpages as part of the app. Check your server output to see what port it's running on (usually something like localhost:5000). We have ours set to run on an Apache/2.4.18 (Ubuntu) Server at powertoken.grouplens.org:443.

In [routes.py](routes.py) you will see a collection of methods that are mapped to URLs (routes). You shouldn't try to manually enter these URLs because some require HTTP data.

In the [templates](templates) folder, you will see a collection of HTML files. These are served and modified by the Python code. The templates with the "user_" prefix are part of the user-facing application, and the templates with the "admin_" prefix are part of the admin-facing application. The [user_fb_login.html](templates/user_fb_login.html) file contains JavaScript that logs the user into Fitbit, goes through the OAuth process, and sends an access code back to the server via the POST method of the `/fb_login` route.

Similar to the routes, manually entering an HTML template might not yield the behavior you expect, because some of the templates are not hard-coded HTML, but populated by the Python code as they are served.

<!--
In the /static folder, you will find the golden egg. The JavaScript file [fb_login.js](static/js/fb_login.js) (which is run from [fb_login.html](templates/fb_login.html)) logs the user into Fitbit, goes through the OATH process, and sends an access code back to the server via the POST method of the /fb_login route. There is probably a more finessed way of doing this, but hey, it works.
-->

Other than the Fitbit login, the user setup code is written in Python, found in [routes.py](routes.py).

The information entered by the user is not saved, only the access tokens and IDs received from the APIs.

## Admin Notes:

[routes.py](routes.py) handles the routing for the admin portion of the application as well.


## Running in Gunicorn

While running the application directly using `python powertoken.py` is fine for testing, in a production setting you will want to run the Flask app in Gunicorn. In the parent directory (on the same level as [powertoken.py](../powertoken.py), you will see the file [wsgi.py](../wsgi.py). From this directory, you can start Gunicorn with the following command:

`gunicorn --bind 127.0.0.1:5000 wsgi --workers 3`

You can vary the number of workers depending on the expected workload of the application. The important thing is that Gunicorn allows the application to serve multiple clients at the same time.

You might want to automate the process of starting Gunicorn by placing the command in a Bash script.


## Tips:

It's best to use a virtualenv to setup Flask; see the Flask documentation for details.

Using the Fitbit API requires additional setup--if you don't have an account and app set up, see the Web API quickstart. This app uses implicit OAuth flow (implemented with JavaScript/HTML), saves the access token to a database on the server, and completes all subsequent API calls in Python.

You may want to keep the Flask server running even when you close your SSH session. In this case, the command `nohup python routes.py &` should do the trick. Should you want to kill the process, you will have to do so manually.

An alternative to using `nohup` is to make use of the Linux `screen` module. Create a new screen with the command `screen -r powertoken` and then run `python routes.py`. When you want to disconnect, type `Ctrl+A d`, and you may now close your SSH session. When you want to reconnect, just type `screen -r powertoken` to reconnect to the powertoken screen.