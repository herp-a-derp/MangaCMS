
import runStatus
runStatus.preloadDicts = False

import calendar
import traceback

import re
import settings
from dateutil import parser
import urllib.parse
import time

import MangaCMS.ScrapePlugins.LoaderBase
class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.Hitomi.Fl"
	plugin_name = "Hitomi Link Retreiver"
	plugin_key    = "hit"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "https://hitomi.la/"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:

			urlPath = '/index-all-{num}.html'.format(num=pageOverride)
			sourceUrl = urllib.parse.urljoin(self.urlBase, urlPath)

			page = self.wg.getSoup(sourceUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from Hitomi!")
			self.log.critical(traceback.format_exc())
			return ""

		return page



	def parseLinkDiv(self, linkdiv):

		if not linkdiv.h1:
			return

		date = linkdiv.find("p", class_="date")
		if not date:
			return

		ret = {}

		lang = "Unknown"

		for row in linkdiv.find_all("tr"):
			if not len(row("td")) == 2:
				continue
			param, val = row("td")
			param = param.get_text().strip()
			val   = val.get_text().strip()


			if param.lower() == "language":

				# Only scrape english TLs and japanese language content.
				# This'll probably miss some other non-japanese content,
				# but they don't seem to have a "translated" tag.
				if val.lower() not in ['english', "n/a"]:
					self.log.info("Skipping item due to language being %s.", val)
					return None
				lang = val.lower()

			if param.lower() == "type":
				ret['series_name']  = val.title()



			# Judge me
			if param.lower() == "tags":
				if "males only" in val.lower() and not "females only" in val.lower():
					self.log.info("Skipping item due to tag 'males only' (%s).", val.replace("\n", " "))
					return None

		if 'series_name' in ret and ret['series_name'] == 'artist CG':
			if 'lang' == 'n/a':
				return None

		ret["origin_name"] = linkdiv.h1.get_text().strip()
		ret["source_id"] = urllib.parse.urljoin(self.urlBase, linkdiv.h1.a["href"])


		pdate = parser.parse(date.get_text())
		ret["posted_at"] = pdate

		return ret

	def get_feed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#

		# self.wg.stepThroughJsWaf("https://hitomi.la/", titleContains="Hitomi.la")

		ret = []

		for x in pageOverride:
			soup = self.loadFeed(x)


			mainSection = soup.find("div", class_="gallery-content")

			doujinLink = mainSection.find_all("div", class_=re.compile("(cg|dj|manga|acg)"), recursive=False)

			for linkLi in doujinLink:
				tmp = self.parseLinkDiv(linkLi)
				if tmp:
					ret.append(tmp)

		return ret




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = DbLoader()
		# dat = run.getFeed(pageOverride=[1])
		# run.do_fetch_feeds()
		for x in range(13500):
			dat = run.get_feed(pageOverride=[x])
			run._process_links_into_db(dat)

