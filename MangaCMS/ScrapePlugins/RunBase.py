

import datetime
import logging
import settings
import psycopg2
import runStatus
import time
import traceback
import abc

import MangaCMS.db as db

class ScraperBase(metaclass=abc.ABCMeta):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta



	@abc.abstractmethod
	def pluginName(self):
		return None

	@abc.abstractmethod
	def loggerPath(self):
		return None

	@abc.abstractmethod
	def feedLoader(self):
		return None

	@abc.abstractmethod
	def contentLoader(self):
		return None


	def __init__(self):
		self.log = logging.getLogger(self.loggerPath)
		self.log.info("Loading %s Runner", self.pluginName)


	def amRunning(self):
		assert isinstance(self.pluginName, str)

		with db.session_context() as sess:
			have = sess.query(db.PluginStatus)                       \
					.filter(db.PluginStatus.name == self.pluginName) \
					.scalar()
			if have:
				return have.running
			return False


	# name           = Column(Text, nullable=False, unique=True, index=True)
	# last_output    = Column(Text)
	# running        = Column(Boolean, nullable=False, default=False)

	# last_run       = Column(DateTime, nullable=False, default=datetime.datetime.min)
	# last_error     = Column(DateTime, nullable=False, default=datetime.datetime.min)
	# run_time       = Column(Interval, nullable=False, default=0)




	def update_status(self,
				pluginName  = None,
				running     = None,
				last_run    = None,
				last_error  = None,
				run_time    = None,
				last_output = None,
			):
		if pluginName is None:
			pluginName = self.pluginName

		with db.session_context() as sess:
			have = sess.query(db.PluginStatus)                       \
					.filter(db.PluginStatus.name == self.pluginName) \
					.scalar()
			if have:
				self.log.info("Have plugin row. Updating")
				if running is not None:
					have.running = running
				if last_run is not None:
					have.last_run = last_run
				if last_error is not None:
					have.last_error = last_error
				if run_time is not None:
					have.run_time = run_time
				if last_output is not None:
					have.last_output = last_output
			else:
				self.log.info("Plugin appears to be new. Adding initial row!")
				new = db.PluginStatus(
						name        = pluginName,
						running     = running,
						last_run    = last_run,
						last_error  = last_error,
						run_time    = run_time,
						last_output = last_output,
					)
				sess.add(new)

	def go(self):
		self.log.info("Executing plugin %s", self.pluginName)
		if self.amRunning():
			self.log.critical("%s is already running! Not launching again!", self.pluginName)
			return
		else:
			self.log.info("%s Started.", self.pluginName)

			run_start = datetime.datetime.now()
			self.update_status(running=True, last_run=run_start)
			try:
				self._go()
			except Exception:
				# If we have a uncaught exception in the plugin, log the exception traceback (which will get logged to
				# the DB), and then re-raise
				self.update_status(running=False, last_error=datetime.datetime.now(), last_output=traceback.format_exc())
				self.log.critical("Uncaught major exception in plugin!")
				self.log.critical("Traceback:")
				for line in traceback.format_exc().split("\n"):
					self.log.critical(line)

				raise

			finally:
				run_stop = datetime.datetime.now()
				self.update_status(running=False, run_time=run_stop-run_start)
				self.log.info("%s finished. Execution time: %s.", self.pluginName, run_stop-run_start)




	def _go(self):

		fl = self.feedLoader()
		fl.do_fetch_feeds()

		time.sleep(3)
		#print "wat", cl

		if not runStatus.run:
			return

		cl = self.contentLoader()
		cl.do_fetch_content()
