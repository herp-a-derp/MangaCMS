
import calendar
import datetime
import traceback

import json
import settings
from dateutil import parser
import urllib.parse
import time

import MangaCMS.ScrapePlugins.LoaderBase
class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.DjM.Fl"
	plugin_name = "DjMoe Link Retreiver"
	plugin_key  = "djm"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "http://doujins.com/"


	shouldCanonize = False

	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 1
		pageOverride -= 1
		pageOverride = max(pageOverride, 0)
		pageOverride = pageOverride * 5

		date = datetime.date.today()
		date = date - datetime.timedelta(days=pageOverride)
		dt = datetime.datetime.combine(date, datetime.time(0))
		newer = int(dt.timestamp())
		older = newer - (60 * 60 * 24 * 7)


		try:
			# They're apparently sniffing cookies now. Fake out the system by loading the container page first.
			dummy_pg = self.wg.getpage("https://doujins.com/")
			data = self.wg.getJson( urllib.parse.urljoin(self.urlBase, "folders?start={older}&end={newer}").format(older=older, newer=newer),
				addlHeaders={'Referer': 'https://doujins.com/'} )
		except urllib.error.URLError:
			self.log.critical("Could not get feed from Doujin Moe!")
			self.log.critical(traceback.format_exc())
			return []

		try:
			self.log.info("done")
		except ValueError:
			self.log.critical("Get did not return JSON like normal!")
			self.log.critical("Returned page contents = %s", data)
			return []

		if not "success" in data or data["success"] != True:
			self.log.error("POST did not return success!")
			self.log.error("Returned JSON string = %s", data)
			return []

		items = data["folders"]
		return items


	def get_feed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		items = self.loadFeed(pageOverride)
		ret = []
		for feedEntry in items:
			item = {}

			try:
				item["origin_name"] = feedEntry["name"]
				item["source_id"]   = feedEntry["token"]
				item["posted_at"]   = parser.parse( feedEntry["date"])
				#self.log.info("date = ", feedEntry['published_parsed'])
				# item['retreivalTime'] = time.time()

				ret.append(item)

			except:
				self.log.info("WAT?")
				traceback.print_exc()

		self.log.info("Found %s releases", len(ret))
		return ret


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		# getHistory()
		run = DbLoader()
		# run.getFeed()
		for x in range(500):
			run.do_fetch_feeds(pageOverride=x)


