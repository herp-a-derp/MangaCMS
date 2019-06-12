
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


	logger_path = "Main.Manga.DoujinOnline.Fl"
	plugin_name = "DoujinOnline Link Retreiver"
	plugin_key  = "dol"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "https://doujinshi.online/"


	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 1

		urlPath = '/page/{num}/'.format(num=pageOverride)
		sourceUrl = urllib.parse.urljoin(self.urlBase, urlPath)

		page = self.wg.getSoup(sourceUrl)

		return page



	def parseLinkDiv(self, linkdiv):


		dated = linkdiv.find("div", class_="dou-date")
		titled = linkdiv.find("div", class_="dou-title")
		langd = linkdiv.find("div", class_="lang-icon")


		if not all([langd, titled, dated]):
			return

		if not langd.img:
			return
		if not langd.img['src'].endswith("en.png"):
			return

		pdate = parser.parse(dated.get_text())

		ret = {}

		ret["origin_name"] = titled.get_text().strip()
		ret["source_id"] = urllib.parse.urljoin(self.urlBase, titled.a["href"])
		ret["posted_at"] = pdate

		return ret

	def get_feed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#

		# self.wg.stepThroughJsWaf("https://DoujinOnline.la/", titleContains="DoujinOnline.la")

		ret = []

		for x in pageOverride:
			soup = self.loadFeed(x)

			doujinLink = soup.find_all("div", class_="dou-list")

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
		# print(dat)
		# run.do_fetch_feeds()

		from concurrent.futures import ThreadPoolExecutor


		def callable_f(baseclass, page):

			dat = baseclass.get_feed(pageOverride=[page])
			baseclass._process_links_into_db(dat)

		print("Doing batch req")
		with ThreadPoolExecutor(max_workers=5) as ex:
			for x in range(1160):
				ex.submit(callable_f, run, x)

