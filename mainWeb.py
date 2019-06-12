#!flask/bin/python
import sys
if sys.version_info < ( 3, 4):
	# python too old, kill the script
	sys.exit("This script requires Python 3.4 or newer!")

import settings
import runStatus

import MangaCMS.lib.logSetup
if __name__ == "__main__":
	MangaCMS.lib.logSetup.initLogging()
	runStatus.preloadDicts = False

import threading
import time
import calendar

import MangaCMS.runtime_flags






import datetime
import sys
import cherrypy
import logging


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore

import nameTools as nt
from MangaCMS.app import app

executors = {
	'main_jobstore': ThreadPoolExecutor(3),
}
job_defaults = {
	'coalesce': True,
	'max_instances': 1
}

jobstores = {
	'main_jobstore' : MemoryJobStore(),
}


def run_server():
	MangaCMS.runtime_flags.IS_FLASK = True

	listen_address = "0.0.0.0"
	listen_port    = 8081

	if not "debug" in sys.argv:
		print("Starting background thread")
		# bk_thread = startBackgroundThread()

	if "debug" in sys.argv:
		print("Running in debug mode.")
		app.run(host=listen_address, port=listen_port, debug=True)
	else:
		print("Running in normal mode.")
		# app.run(host=listen_address, port=listen_port, processes=10)
		# app.run(host=listen_address, port=listen_port, threaded=True)



		def fixup_cherrypy_logs():
			loggers = logging.Logger.manager.loggerDict.keys()
			for name in loggers:
				if name.startswith('cherrypy.'):
					print("Fixing %s." % name)
					logging.getLogger(name).propagate = 0


		cherrypy.tree.graft(app, "/")
		cherrypy.server.unsubscribe()

		# Instantiate a new server object
		server = cherrypy._cpserver.Server()
		# Configure the server object
		server.socket_host = listen_address

		server.socket_port = listen_port
		server.thread_pool = 8

		# For SSL Support
		# server.ssl_module            = 'pyopenssl'
		# server.ssl_certificate       = 'ssl/certificate.crt'
		# server.ssl_private_key       = 'ssl/private.key'
		# server.ssl_certificate_chain = 'ssl/bundle.crt'

		# Subscribe this server
		server.subscribe()

		# fixup_cherrypy_logs()

		if hasattr(cherrypy.engine, 'signal_handler'):
			cherrypy.engine.signal_handler.subscribe()
		# Start the server engine (Option 1 *and* 2)
		cherrypy.engine.start()
		cherrypy.engine.block()
		# fixup_cherrypy_logs()



	print()
	print("Interrupt!")
	# if not "debug" in sys.argv:
	# 	print("Joining on background thread")
	# 	flags.RUNSTATE = False
	# 	bk_thread.join()

	# print("Thread halted. App exiting.")
	#
def run_web():

	nt.dirNameProxy.startDirObservers()


	sched = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
	sched.start()


	x = 60
	for name, classInstance in nt.__dict__.items():

		# look up all class instances in nameTools. If they have the magic attribute "NEEDS_REFRESHING",
		# that means they support scheduling, so schedule the class in question.
		# To support auto-refreshing, the class needs to define:
		# cls.NEEDS_REFRESHING = {anything, just checked for existance}
		# cls.REFRESH_INTERVAL = {number of seconds between refresh calls}
		# cls.refresh()        = Call to do the refresh operation. Takes no arguments.
		#
		if  isinstance(classInstance, type) or not hasattr(classInstance, "NEEDS_REFRESHING"):
			continue

		sched.add_job(classInstance.refresh,
					trigger='interval',
					seconds=classInstance.REFRESH_INTERVAL,
					start_date=datetime.datetime.now()+datetime.timedelta(seconds=20+x),
					jobstore='main_jobstore')

		x += 60*2.5


	# It looks like cherrypy installs a ctrl+c handler, so I don't need to.
	run_server()



if __name__ == "__main__":
	started = False
	if not started:
		started = True
		run_web()
