
import runStatus
runStatus.preloadDicts = False



import urllib.parse
import time
import datetime
import calendar
import parsedatetime
import settings

import MangaCMS.ScrapePlugins.LoaderBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):

	logger_path = "Main.Manga.Mh.Fl"
	plugin_name = "MangaHere Link Retreiver"
	plugin_key = "mh"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	urlBase    = "http://www.mangahere.co/"
	seriesBase = "http://www.mangahere.co/latest/"


	def getUpdatedSeries(self, url):
		ret = set()

		soup = self.wg.getSoup(url)

		if soup.find("div", class_='manga_updates'):
			mainDiv = soup.find("div", class_='manga_updates')
		else:
			raise ValueError("Could not find listing table?")

		for child in mainDiv.find_all("dl"):
			if child.dt:
				seriesUrl = urllib.parse.urljoin(self.urlBase, child.dt.a['href'])
				ret.add(seriesUrl)


		self.log.info("Found %s series", len(ret))

		return ret

	def getUpdatedSeriesPages(self):
		# Historical stuff goes here, if wanted.
		self.log.info( "Loading MangaHere Items")

		pages = self.getUpdatedSeries(self.seriesBase)

		self.log.info("Found %s total items", len(pages))
		return pages

	# Check retreived page to see if it has a mature content warning
	# Step through if it does.
	# Returns page with actual content, either way
	def checkAdult(self, soup):
		adultPassThrough = soup.find("a", id='aYes')
		if not adultPassThrough:
			return soup

		self.log.info("Adult pass-through page. Stepping through")
		confirmLink = adultPassThrough['href']
		return self.wg.getSoup(confirmLink)


	def getSeriesInfoFromSoup(self, soup):
		# Should probably extract tagging info here. Laaaaazy
		# MangaUpdates interface does a better job anyways.
		titleA = soup.find("h1", class_='title')
		return {"series_name": titleA.get_text().title()}

	def getChaptersFromSeriesPage(self, soup):
		table = soup.find('div', class_='detail_list')

		items = []
		for row in table.find_all("li"):
			if not row.a:
				continue  # Skip the table header row

			chapter = row.find("span", class_='left')
			date    = row.find("span", class_='right')


			item = {}

			# Name is formatted "{series_name} {bunch of spaces}\n{chapterName}"
			# Clean up that mess to "{series_name} - {chapterName}"
			name = chapter.get_text().strip()
			name = name.replace("\n", " - ")
			while "  " in name:
				name = name.replace("  ", " ")

			item["origin_name"] = name
			item["source_id"]  = urllib.parse.urljoin(self.urlBase, chapter.a['href'])
			dateStr = date.get_text().strip()
			itemDate, status = parsedatetime.Calendar().parse(dateStr)
			if status != 1:
				continue

			item['posted_at'] = datetime.datetime.fromtimestamp(calendar.timegm(itemDate))
			item["last_checked"] = datetime.datetime.now()
			items.append(item)


		return items

	def getChapterLinkFromSeriesPage(self, seriesUrl):
		ret = []
		soup = self.wg.getSoup(seriesUrl)
		soup = self.checkAdult(soup)

		seriesInfo = self.getSeriesInfoFromSoup(soup)

		chapters = self.getChaptersFromSeriesPage(soup)
		for chapter in chapters:

			for key, val in seriesInfo.items(): # Copy series info into each chapter
				chapter[key] = val

			ret.append(chapter)

		self.log.info("Found %s items on page for series '%s'", len(ret), seriesInfo['series_name'])

		return ret

	def get_feed(self):
		toScan = self.getUpdatedSeriesPages()

		ret = []

		for url in toScan:
			items = self.getChapterLinkFromSeriesPage(url)
			for item in items:
				if item in ret:
					raise ValueError("Duplicate items in ret?")
				ret.append(item)
			self._process_links_into_db(ret)
			ret = []
		return ret


	def setup(self):
		cf_ok = self.wg.stepThroughJsWaf("http://www.mangahere.co/", titleContains='Manga Here - ')
		self.log.info("CF Access return value: %s", cf_ok)
		if not cf_ok:
			raise ValueError("Could not access site due to cloudflare protection.")


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		fl = FeedLoader()
		# print(fl.getUpdatedSeriesPages())
		# print(fl.getAllItems())
		# fl.resetStuckItems()
		fl.do_fetch_feeds()
		# fl.getChapterLinkFromSeriesPage("http://www.mangahere.co/manga/penguin_loves_mev/")
		# fl.getSeriesUrls()

		# fl.getAllItems()

