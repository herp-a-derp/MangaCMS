
import runStatus
runStatus.preloadDicts = False




import urllib.parse
import datetime
import time
import calendar
import dateutil.parser
import settings

import MangaCMS.ScrapePlugins.LoaderBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):



	logger_path = "Main.Manga.Ze.Fl"
	plugin_name = "Comic-Zenon Magazine Link Retreiver"
	plugin_key = "ze"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	url_base    = "http://www.manga-audition.com/comic-zenon/"

	def getSeriesPages(self):

		self.log.info( "Loading ComicZenon Items")

		ret = []

		soup = self.wg.getSoup(self.url_base)

		main_chunk = soup.find_all("div", class_='ZenonComics')
		for chunk in main_chunk:
			for url_tag in chunk.find_all("a"):
				url = url_tag['href']
				if url.startswith("#"):
					continue
				if not url.startswith("http://comic.manga-audition.com"):
					ret.append(url)

		return ret

	def getChaptersFromSeriesPage(self, soup):


		items = []
		for row in soup.find_all("img", class_='ReadBtn'):

			item = {}
			parent = row.parent
			if parent is not None:
				url = parent.get("href", None)
				if url:
					item["source_id"]  = url
					item['posted_at'] = datetime.datetime.now()
					items.append(item)

		return items

	def getChapterLinksFromSeriesPage(self, seriesUrl):
		ret = []
		soup = self.wg.getSoup(seriesUrl)


		ret = self.getChaptersFromSeriesPage(soup)
		self.log.info("Found %s items on page '%s'", len(ret), seriesUrl)

		return ret

	def get_feed(self):
		toScan = self.getSeriesPages()
		toScan = set(toScan)
		ret = []

		for url in toScan:
			if not 'www.manga-audition.com' in url:
				continue

			items = self.getChapterLinksFromSeriesPage(url)
			for item in items:
				if item in ret:
					raise ValueError("Duplicate items in ret?")
				ret.append(item)
		return ret


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		fl = FeedLoader()
		fl.do_fetch_feeds()
		# fl.getChapterLinksFromSeriesPage('https://www.manga-audition.com/comic-zenon/ikusa-no-ko-by-tetsuo-hara/')
		# fl.getSeriesUrls()

		# fl.getAllItems()

