
import runStatus
import json
runStatus.preloadDicts = False



import http.cookiejar
import urllib.parse
import time
import calendar
import parsedatetime
import datetime
import settings

import MangaCMS.ScrapePlugins.LoaderBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):

	logger_path  = "Main.Manga.MDx.Fl"
	plugin_name  = "MangaDex Link Retreiver"
	plugin_key   = "mdx"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	urlBase    = "https://mangadex.org/"
	seriesBase = "https://mangadex.org/updates"

	def setup(self):
		now = int(time.time() * 1000)

		cookie = http.cookiejar.Cookie(
				name               = 'mangadex_h_toggle',
				value              = '1',

				port               = '80',
				domain             = 'mangadex.org',
				path               = "/",
				expires            = 9999999999,

				version            = 1,
				port_specified     = None,
				domain_specified   = None,
				domain_initial_dot = None,
				path_specified     = None,
				secure             = False,
				discard            = False,
				comment            = None,
				comment_url        = None,
				rest               = None,
			)

		self.wg.cj.set_cookie(cookie)
		self.wg.getpage("https://mangadex.org")


	def getUpdatedSeries(self, url):
		ret = set()

		soup = self.wg.getSoup(url)

		if soup.find("div", class_='table-responsive'):
			mainDiv = soup.find("div", class_='table-responsive')
		else:
			raise ValueError("Could not find listing table?")

		for child in mainDiv.find_all("a", class_='manga_title'):
			if child:
				seriesUrl = urllib.parse.urljoin(self.urlBase, child['href'])
				ret.add(seriesUrl)


		self.log.info("Found %s series", len(ret))

		if 'https://mangadex.org/manga/47/test' in ret:
			ret.remove("https://mangadex.org/manga/47/test")

		return ret


	def getUpdatedSeriesPages(self, history=False):
		# Historical stuff goes here, if wanted.

		self.log.info("Loading MangaDex Items")

		url = self.seriesBase
		if history:
			url = url + "/{}/".format(history)

		pages = self.getUpdatedSeries(url)



		self.log.info("Found %s total items", len(pages))
		return pages



	def getSeriesInfoFromSoup(self, soup):
		# Should probably extract tagging info here. Laaaaazy
		# MangaUpdates interface does a better job anyways.
		titleA = soup.find("h6", class_='card-header')
		if not titleA:
			return None
		return {"series_name": titleA.get_text(strip=True)}

	def getChaptersFromSeriesPage(self, soup):
		sname = soup.find("h6", class_='card-header').get_text(strip=True)

		# import pdb
		# pdb.set_trace()

		items = []
		for row in soup.find_all("div", class_="chapter-row"):
			if not row.a:
				continue  # Skip the table header row


			tds = row.find_all("div", recursive=False)
			if len(tds) != 9:
				self.log.warning("Invalid number of table entries: %s", len(tds))
				self.log.warning("Row: %s", row)
				self.log.warning("Subsections: %s", json.dumps([str(tmp) for tmp in tds]))
				continue

			dummy_something,      \
				chapter_name,     \
				dummy_discussion, \
				ultime,           \
				dummy_nfi,        \
				lang,             \
				group,            \
				dummy_uploader,   \
				dummy_views,      \
					= tds

			lang = lang.find("span", class_='flag')['title']

			if lang != DOWNLOAD_ONLY_LANGUAGE:
				self.log.warning("Skipping non-english item: %s", lang)
				continue

			item = {}

			# Name is formatted "{seriesName} {bunch of spaces}\n{chapterName}"
			# Clean up that mess to "{seriesName} - {chapterName}"
			name = chapter_name.get_text().strip()
			name = name.replace("\n", " - ")
			while "  " in name:
				name = name.replace("  ", " ")

			name = "{} - {} [{}, {}]".format(sname, name, "MangaDex", group.get_text(strip=True))

			item["origin_name"] = name
			item["source_id"]  = urllib.parse.urljoin(self.urlBase, chapter_name.a['href'])
			dateStr = ultime.get_text(strip=True)

			# No idea how this was happening.
			dateStr = dateStr.replace("minago",    "minutes ago")
			dateStr = dateStr.replace("minsago",   "minutes ago")
			dateStr = dateStr.replace("hrago",     "hours ago")
			dateStr = dateStr.replace("hrsago",    "hours ago")
			dateStr = dateStr.replace("dayago",    "days ago")
			dateStr = dateStr.replace("daysago",   "days ago")
			dateStr = dateStr.replace("moago",     "months ago")
			dateStr = dateStr.replace("mosago",    "months ago")
			dateStr = dateStr.replace("yearago",   "months ago")
			dateStr = dateStr.replace("yearsago",  "months ago")

			itemDate, status = parsedatetime.Calendar().parse(dateStr)
			if status < 1:
				self.log.error("Failed to parse date '%s': %s->%s", dateStr, status, itemDate)
				continue

			item['posted_at'] = datetime.datetime(*itemDate[:6])

			items.append(item)


		return items

	def getChapterLinkFromSeriesPage(self, seriesUrl):
		ret = []
		soup = self.wg.getSoup(seriesUrl)

		seriesInfo = self.getSeriesInfoFromSoup(soup)
		if not seriesInfo:
			self.log.error("No series info on page '%s'", seriesUrl)
			return ret

		chapters = self.getChaptersFromSeriesPage(soup)
		for chapter in chapters:

			for key, val in seriesInfo.items(): # Copy series info into each chapter
				chapter[key] = val

			ret.append(chapter)

		self.log.info("Found %s items on page for series '%s'", len(ret), seriesInfo['series_name'])

		return ret

	def get_feed(self, history=False):
		toScan = self.getUpdatedSeriesPages(history)


		for url in toScan:
			ret = []
			items = self.getChapterLinkFromSeriesPage(url)
			for item in items:
				if item in ret:
					raise ValueError("Duplicate items in ret?")
				ret.append(item)

			self._process_links_into_db(ret)

		return []

	def get_history(self):
		idx = 0
		found = 0
		have_spages = True

		while have_spages:
			soup = self.wg.getSoup("https://mangadex.org/titles/{idx}".format(idx=idx))
			idx += 100
			main_div = soup.find("div", class_='row')
			tmp_list = []
			if main_div:
				divs = main_div.find_all("div", class_='col-sm-6')
				self.log.info("Found %s series links")
				for row in divs:
					if row.a:
						surl = urllib.parse.urljoin(self.urlBase, row.a['href'])
						tmp_list.append(surl)

						ret = []
						items = self.getChapterLinkFromSeriesPage(surl)
						for item in items:
							if item in ret:
								raise ValueError("Duplicate items in ret?")
							ret.append(item)
							found += 1
						self._process_links_into_db(ret)
						self.log.info("Found %s items so far", found)


			have_spages = len(tmp_list)




		# self.log.info("Found %s total items", len(pages))
		# return pages


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		fl = FeedLoader()
		# fl.setup()
		# fl.get_history()
		for x in range(1, 20):
			fl.get_feed(x)
			time.sleep(15)
		# fl.do_fetch_feeds()
		# print(fl.getUpdatedSeriesPages())
		# print(fl.getAllItems())
		# fl.resetStuckItems()
		# cl = fl.getChapterLinkFromSeriesPage("https://mangadex.org/manga/29247/dame-na-kanojo-wa-amaetai")
		# cl = fl.getChapterLinkFromSeriesPage("https://mangadex.org/manga/19969")
		# cl = fl.getChapterLinkFromSeriesPage("https://mangadex.org/manga/9134")
		# print(cl)
		# fl.getSeriesUrls()

		# print("Links: ", cl)
		# fl.getAllItems()

