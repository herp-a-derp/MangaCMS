
import runStatus
runStatus.preloadDicts = False


import calendar
import datetime
import traceback

import bs4
import settings
from dateutil import parser
import urllib.parse
import time

import MangaCMS.ScrapePlugins.LoaderBase
class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.Pururin.Fl"
	plugin_name = "Pururin Link Retreiver"
	plugin_key  = "pu"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	retreivalThreads = 2

	urlBase = "http://pururin.io/"

	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind Pururin's path scheme.
			if pageOverride > 1:

				urlPath = '/browse/newest?page={num}'.format(num=pageOverride)
				pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)
			else:
				# First page is just the bare URL. It /looks/ like they're blocking the root page by direct path.
				pageUrl = self.urlBase

			print("Fetching page at", pageUrl)
			page = self.wg.getpage(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from Pururin!")
			self.log.critical(traceback.format_exc())
			return ""

		return page



	def parseLinkLi(self, linkdiv):
		ret = {}
		ret["origin_name"] = " / ".join(linkdiv.find("div", class_='title').strings) # Messy hack to replace <br> tags with a ' / "', rather then just removing them.
		ret["source_id"] = urllib.parse.urljoin(self.urlBase, linkdiv["href"])
		ret["posted_at"] = datetime.datetime.now()

		return ret

	def get_feed(self, pageOverride=[None]):
		# for item in items:
		# 	self.log.info(item)
		#


		ret = []

		for x in pageOverride:
			page = self.loadFeed(x)

			soup = bs4.BeautifulSoup(page, "lxml")

			mainSection = soup.find("div", class_="row-gallery")

			doujinLink = mainSection.find_all("a", class_="card-gallery")

			for linkLi in doujinLink:
				tmp = self.parseLinkLi(linkLi)
				ret.append(tmp)

		return ret



	def setup(self):
		self.wg.stepThroughJsWaf(self.urlBase, titleContains="Pururin")





if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = DbLoader()
		run.do_fetch_feeds()
		for x in range(1000):
			dat = run.get_feed(pageOverride=[x])
			print("Found %s items" % len(dat))
			run._process_links_into_db(dat)

