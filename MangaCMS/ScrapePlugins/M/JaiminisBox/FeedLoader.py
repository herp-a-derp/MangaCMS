

import MangaCMS.lib.logSetup
import runStatus
if __name__ == "__main__":
	MangaCMS.lib.logSetup.initLogging()
	runStatus.preloadDicts = False

import parsedatetime


import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import datetime

import MangaCMS.ScrapePlugins.LoaderBase
import nameTools as nt

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):

	logger_path = "Main.Manga.Jb.Fl"
	plugin_name = "Jaimini's Box Feed Loader"
	plugin_key  = "jb"

	is_manga    = True
	is_hentai   = False
	is_book     = False

	url_base    = "https://jaiminisbox.com/"
	latest_changes = "https://jaiminisbox.com/reader/latest/{num}/"

	def extractItemInfo(self, soup):

		ret = {}

		titleH = soup.find("h3", class_='subj')
		ret["title"] = titleH.get_text().strip()
		return ret


	def getItemsForSeries(self, url):
		ret = []

		soup = self.wg.getSoup(url)

		if soup.find("div", class_='panel'):
			mainDiv = soup.find("div", class_='panel')
		else:
			raise ValueError("Could not find item container?")

		meta = mainDiv.find("div", class_="large comic")
		series_title = meta.find("h1").get_text(strip=True)
		chap_div = mainDiv.find("div", class_='list')

		for entry in chap_div.find_all("div", class_='element'):  # Iterate over only tag entryren

			item = {}

			dllink = entry.find("div", class_='icon_wrapper').a['href']
			post_date_section = list(entry.find("div", class_='meta_r').children)

			item["source_id"]     = dllink

			timestr = post_date_section[-1].strip()


			itemDate, status = parsedatetime.Calendar().parse(timestr)

			if status >= 1:
				item['posted_at'] = datetime.datetime(*itemDate[:6])
			else:
				self.log.warning("Parsing relative date '%s' failed (%s). Using current timestamp.", timestr, status)
				item['posted_at'] = datetime.datetime.now()



			item["series_name"]   = series_title
			item["last_checked"]  = datetime.datetime.now()

			titleDiv = entry.find("div", class_='title')

			title = titleDiv.get_text(strip=True)
			if titleDiv.small:
				title += ' {%s}' % titleDiv.small.text.strip()

			item["origin_name"] = title

			ret.append(item)

		self.log.info("Found %s chapter releases for series %s", len(ret), series_title)

		return ret

	def getItems(self, url):

		releases = []
		checked = set()
		checked_releases = set()
		soup = self.wg.getSoup(url)
		entries = soup.find_all("div", class_='group')
		for entry in entries:
			item = entry.find("div", class_="title")
			surl = item.a['href']
			if surl not in checked:
				series_items = self.getItemsForSeries(surl)
				checked.add(surl)

				for subentry in series_items:
					if subentry['source_id'] not in checked_releases:

						releases.append(subentry)
						checked_releases.add(subentry['source_id'])

		return releases

	def get_feed(self, historical=False):
		# for item in items:
		# 	self.log.info( item)

		self.log.info( "Loading Dynasty Scans Items")

		ret = []
		cnt = 1
		while 1:


			pages = self.getItems(self.latest_changes.format(num=cnt))


			if not pages:
				break

			for page in pages:
				ret.append(page)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

			if not historical:
				break

			cnt += 1

		self.log.info("Found %s total items", len(ret))
		return ret

if __name__ == '__main__':
	fl = FeedLoader()
	print("fl", fl)
	fl.do_fetch_feeds()
	# fl.getItems("https://jaiminisbox.com/reader/latest/1/")
	# fl.getItemsForSeries("https://jaiminisbox.com/reader/series/we-can-t-study/")
	# fl.do_fetch_feeds(historical=True)
	# fl.getSeriesUrls()
	# fl.getAllItems()
	# items = fl.getItemPages('http://www.webtoons.com/episodeList?titleNo=78')
	# print("Items")
	# for item in items:
	# 	print("	", item)

