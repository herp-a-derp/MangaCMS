

# from guess_language import guess_language

import markdown
import os.path

from flask import render_template
from flask import send_file
from flask import g

import traceback


from MangaCMS import lib
import MangaCMS.app.sub_views

from MangaCMS.app import app
from MangaCMS import db as database



@app.before_request
def before_request():
	g.locale = 'en'
	g.session = database.new_session()

@app.after_request
def add_headers(response):
	response.cache_control.public = True
	response.cache_control.max_age = 300
	return response


# @app.teardown_appcontext
@app.teardown_request
def teardown_request(response):
	print("Closing request!")
	try:
		g.session.commit()
	except Exception:
		g.session.rollback()

	g.session.close()
	g.session.expunge_all()
	database.delete_db_session(g.session)
	del g.session



@app.errorhandler(404)
def not_found_error(dummy_error):
	print("404. Wat?")
	return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(dummy_error):
	print("Internal Error!")
	print(dummy_error)
	print(traceback.format_exc())
	# print("500 error!")
	return render_template('500.html'), 500




@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():

	interesting = ""
	if os.path.exists("todo.md"):
		with open("todo.md", "r") as fp:
			raw_text = fp.read()
		interesting = markdown.markdown(raw_text, extensions=["mdx_linkify"])

	return render_template('index.html',
						   title               = 'Home',
						   interesting_links   = interesting,
						   )

@app.route('/favicon.ico')
def sendFavIcon():
	return send_file(
		"./static/favicon.ico",
		conditional=True
		)



