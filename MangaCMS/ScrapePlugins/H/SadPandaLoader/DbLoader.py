

import traceback

import re
import copy
import urllib.parse
import time
import calendar
import random
import runStatus

import dateutil.parser

import nameTools as nt
import settings
from . import LoginMixin
import MangaCMS.ScrapePlugins.LoaderBase

class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase, LoginMixin.ExLoginMixin):


	logger_path = "Main.Manga.SadPanda.Fl"
	plugin_name = "SadPanda Link Retreiver"
	plugin_key  = "sp"
	is_manga    = False
	is_hentai   = True
	is_book     = False


	urlBase = "https://exhentai.org/"
	urlFeed = "https://exhentai.org/?page={num}&f_search={search}"


	# -----------------------------------------------------------------------------------
	# The scraping parts
	# -----------------------------------------------------------------------------------



	def loadFeed(self, tag,
				pageOverride=None,
				includeExpunge=False,
				includeLowPower=False,
				includeDownvoted=False
			):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 0  # Pages start at zero. Yeah....
		try:
			# tag = tag.replace(" ", "+")
			tag = urllib.parse.quote_plus(tag)
			pageUrl = self.urlFeed.format(search=tag, num=pageOverride)
			if includeExpunge:
				pageUrl = pageUrl + '&f_sh=on'
			if includeLowPower:
				pageUrl = pageUrl + '&f_sdt1=on'
			if includeDownvoted:
				pageUrl = pageUrl + '&f_sdt2=on'
			soup = self.wg.getSoup(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from SadPanda!")
			self.log.critical(traceback.format_exc())
			return None

		# with open("sp_search_{}_{}.html".format(nt.makeFilenameSafe(tag), time.time()), "w") as fp:
		# 	fp.write(soup.prettify())


		return soup


	def getUploadTime(self, dateStr):
		# ParseDatetime COMPLETELY falls over on "YYYY-MM-DD HH:MM" formatted strings. Not sure why.
		# Anyways, dateutil.parser.parse seems to work ok, so use that.
		updateDate = dateutil.parser.parse(dateStr, yearfirst=True)
		# ret = calendar.timegm(updateDate.timetuple())

		# # Patch times for the local-GMT offset.
		# # using `calendar.timegm(time.gmtime()) - time.time()` is NOT ideal, but it's accurate
		# # to a second or two, and that's all I care about.
		# gmTimeOffset = calendar.timegm(time.gmtime()) - time.time()
		# ret = ret - gmTimeOffset
		return updateDate



	def parseItem(self, inRow):
		ret = {}
		if len(inRow.find_all("td")) != 4:
			if inRow.find("th"):
				return None
			self.log.warning("Wrong number of TDs!")
			print(inRow)
			return None
		itemType, pubTr, name, uploader = inRow.find_all("td")

		# Do not download any galleries we uploaded.
		if uploader.get_text().lower().strip() == settings.sadPanda['login'].lower():
			return None

		category = itemType.get_text()
		if category.lower() in settings.sadPanda['sadPandaExcludeCategories']:
			self.log.info("Excluded category: '%s'. Skipping.", category)
			return False


		ret['series_name'] = category.title()

		if ret['series_name'].lower().startswith("artist - "):
			return False
		if ret['series_name'].lower().startswith("artist archives ::: "):
			return False
		if ret['series_name'].lower().startswith("artist galleries ::: "):
			return False
		if ret['series_name'].lower().startswith("artist: "):
			return False
		if ret['series_name'].lower().startswith("[pixiv] "):
			return False

		# If there is a torrent link, decompose it so the torrent link doesn't
		# show up in our parsing of the content link.
		if pubTr.find("div", class_='gldown'):
			pubTr.find("div", class_='gldown').decompose()

		pubDate = pubTr.find("div", id=re.compile("posted_\d+"))

		for div in name.find_all("div", class_='gt'):
			div.decompose()

		namediv = name.find("div", class_='glink')

		ret['source_id']   = name.a['href']
		ret['origin_name'] = namediv.get_text().strip()
		ret['posted_at']   = self.getUploadTime(pubDate.get_text())


		if ret['origin_name'].lower().startswith("artist - "):
			return False
		if ret['origin_name'].lower().startswith("artist archives ::: "):
			return False
		if ret['origin_name'].lower().startswith("artist galleries ::: "):
			return False
		if ret['origin_name'].lower().startswith("artist: "):
			return False
		if ret['origin_name'].lower().startswith("[pixiv] "):
			return False

		return ret

	def get_feed(self, searchTag,
				includeExpunge=False,
				includeLowPower=False,
				includeDownvoted=False,
				pageOverride=None
			):
		ret = []

		self.log.info("Loading feed for search: '%s'", searchTag)
		soup = self.loadFeed(searchTag, pageOverride, includeExpunge, includeLowPower, includeDownvoted)

		itemTable = soup.find("table", class_="itg")

		if not itemTable:
			return []

		rows = itemTable.find_all("tr")
		self.log.info("Found %s rows on page.", len(rows))
		for row in rows:

			item = self.parseItem(row)
			if item:
				ret.append(item)

		return ret

	# TODO: Add the ability to re-acquire downloads that are
	# older then a certain age.
	# We have to override the parent class here, since we're doing some more complex stuff.
	def do_fetch_feeds(self, history=1):
		self._resetStuckItems()
		self.checkLogin()
		if not self.checkExAccess():
			raise ValueError("Cannot access ex! Wat?")

		for searchTag, includeExpunge, includeLowPower, includeDownvoted in settings.sadPanda['sadPandaSearches']:
			for old_idx in range(history):
				dat = self.get_feed(searchTag, includeExpunge, includeLowPower, includeDownvoted, pageOverride=old_idx)
				self._process_links_into_db(dat)

				sleeptime = random.randrange(5, 60)
				self.log.info("Sleeping %s seconds.", sleeptime)
				for dummy_x in range(sleeptime):
					time.sleep(1)
					if not runStatus.run:
						self.log.info( "Breaking due to exit flag being set")
						return




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		# login()
		run = DbLoader()
		run.checkLogin()
		run.do_fetch_feeds(history=5)


