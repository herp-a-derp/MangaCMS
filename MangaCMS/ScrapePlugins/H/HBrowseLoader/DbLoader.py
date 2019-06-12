
import runStatus
runStatus.preloadDicts = False


import calendar
import traceback
import datetime

import bs4
import settings
from dateutil import parser
import urllib.parse
import time
import calendar

import MangaCMS.ScrapePlugins.LoaderBase

class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.HBrowse.Fl"
	plugin_name = "H-Browse Link Retreiver"
	plugin_key  = "hb"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "http://www.hbrowse.com/"
	urlFeed = "http://www.hbrowse.com/list"


	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			# I really don't get the logic behind HBrowse's path scheme.
			urlPath = '/list/{num}'.format(num=pageOverride)
			pageUrl = urllib.parse.urljoin(self.urlBase, urlPath)

			page = self.wg.getpage(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from HBrowse!")
			self.log.critical(traceback.format_exc())
			return ""

		return page



	def parseItem(self, row, timestamp):
		ret = {}
		ret['posted_at'] = timestamp
		ret['source_id'] = urllib.parse.urljoin(self.urlBase, row.a["href"])
		titleTd = row.find("td", class_='recentTitle')
		ret['origin_name'] = titleTd.get_text()


		return ret

	def extractDate(self, row):
		text = row.get_text(strip=True)
		try:
			date = parser.parse(text)
		except ValueError:
			self.log.warning("Failed to parse date string: %s", text)
			date = datetime.datetime.now()
		return date

	def get_feed(self, pageOverride=None):
		# for item in items:
		# 	self.log.info(item)
		#

		page = self.loadFeed(pageOverride)

		soup = bs4.BeautifulSoup(page, "lxml")

		itemTable = soup.find("table", id="recentTable")

		rows = itemTable.find_all("tr")

		ret = []
		for row in rows:

			if row.find("td", class_='recentDate'):
				curTimestamp = self.extractDate(row)

			elif row.find("td", class_='recentTitle'):
				# curTimestamp is specifically not pre-defined, because I want to fail noisily if I try
				# to parse a link row before seeing a valid date
				item = self.parseItem(row, curTimestamp)

				if 'origin_name' in item:
					# If cloudflare is fucking shit up, just try to get the title from the title tag.
					if r"[email\xa0protected]" in item['origin_name'] or r'[email protected]' in item['origin_name']:
						item['origin_name'] = soup.title.get_text().split(" by ")[0]
				else:
					item['origin_name'] = soup.title.get_text().split(" by ")[0]


				ret.append(item)



		return ret



def getHistory():

	run = DbLoader()
	for x in range(400):
		dat = run.get_feed(pageOverride=x)
		run._process_links_into_db(dat)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		getHistory()
		# run = DbLoader()
		# run.do_fetch_feeds()

