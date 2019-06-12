
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



	logger_path  = "Main.Manga.Mzk.Fl"
	plugin_name  = "MangaZuki Link Retreiver"
	plugin_key   = "mzk"
	is_manga    = True
	is_hentai   = False
	is_book     = False

	urlBase    = "https://mangazuki.co/"
	seriesBase = "https://mangazuki.co/manga-list"


	def getSeriesListing(self):
		self.log.info( "Loading MangaZuki Items")

		ret = set()
		soup = self.wg.getSoup(self.seriesBase)

		if soup.find("div", class_='type-content'):
			mainDiv = soup.find("div", class_='type-content')
		else:
			raise ValueError("Could not find listing table?")

		for child in mainDiv.find_all("div", class_='media'):
			if child:
				seriesUrl = urllib.parse.urljoin(self.urlBase, child.a['href'])
				ret.add(seriesUrl)


		self.log.info("Found %s series", len(ret))

		return ret



	def getChaptersFromSeriesPage(self, soup):

		titleA = soup.find("h2", class_='widget-title')
		series_name = titleA.get_text(strip=True)

		table = soup.find('ul', class_='chapters')

		items = []
		for row in table.find_all("li"):
			if not row.a:
				continue  # Skip the table header row

			chapter = row.find("h3", class_='chapter-title-rtl')
			ul_date = row.find("div", class_='date-chapter-title-rtl')
			dl_link    = row.find("div", class_='action')

			timestr = ul_date.get_text(strip=True)
			itemDate, status = parsedatetime.Calendar().parse(timestr)



			item = {}

			# Name is formatted "{seriesName} {bunch of spaces}\n{chapterName}"
			# Clean up that mess to "{seriesName} - {chapterName}"
			name = chapter.get_text().strip()
			name = name.replace("\n", " - ")
			while "  " in name:
				name = name.replace("  ", " ")

			item["series_name"]    = series_name
			item["origin_name"]    = name
			item["source_id"]     = urllib.parse.urljoin(self.urlBase, dl_link.a['href'])

			if status >= 1:
				item['posted_at'] = datetime.datetime(*itemDate[:6])
			else:
				self.log.warning("Parsing relative date '%s' failed (%s). Using current timestamp.", timestr, status)
				item['posted_at'] = datetime.datetime.now()


			items.append(item)


		return series_name, items

	def getChapterLinkFromSeriesPage(self, seriesUrl):
		ret = []
		soup = self.wg.getSoup(seriesUrl)
		# soup = self.checkAdult(soup)

		series_name, chapters = self.getChaptersFromSeriesPage(soup)
		for chapter in chapters:


			ret.append(chapter)

		self.log.info("Found %s items on page for series '%s'", len(ret), series_name)

		return ret

	def get_feed(self):
		toScan = self.getSeriesListing()

		ret = []

		for url in toScan:
			items = self.getChapterLinkFromSeriesPage(url)
			for item in items:
				if item in ret:
					raise ValueError("Duplicate items in ret?")
				ret.append(item)

		return ret



if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = FeedLoader()
		fl.do_fetch_feeds()
		# print(fl.getSeriesListingPages())
		# print(fl.getSeriesListing())
		# fl.resetStuckItems()
		# fl.go()
		# fl.getChapterLinkFromSeriesPage("https://mangazuki.co/manga/hcampus")
		# fl.getChapterLinkFromSeriesPage("https://mangazuki.co/manga/perfect-half")
		# fl.getSeriesUrls()

		# fl.getAllItems()

