

import urllib.parse
import datetime
import settings
import urllib.error
import dateutil.parser

import runStatus
import MangaCMS.ScrapePlugins.LoaderBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):



	logger_path = "Main.Manga.Ki.Fl"
	plugin_name = "Kiss Manga Link Retreiver"
	plugin_key  = "ki"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	urlBase    = "http://kissmanga.com/"
	seriesBase = "http://kissmanga.com/MangaList/LatestUpdate?page={num}"


	def getUpdatedSeries(self, url):
		ret = set()

		# This is probably a bit brittle. What the hell.
		end = \
'''<script type="text/javascript" src="../../Scripts/jqueryTooltip.js"></script>
Not found
<script type="text/javascript">'''
		if end in ret:
			return ret

		soup = self.wg.getSoup(url)

		if soup.find("table", class_='listing'):
			mainDiv = soup.find("table", class_='listing')
		else:
			raise ValueError("Could not find listing table?")




		for child in mainDiv.find_all("tr"):
			tds = child.find_all("td")
			if len(tds) != 2:
				# Table header - skip it
				continue

			series, dummy_release = tds

			seriesUrl = urllib.parse.urljoin(self.urlBase, series.a['href'])
			ret.add(seriesUrl)



		self.log.info("Found %s series", len(ret))

		return ret


	def getUpdatedSeriesPages(self, historical=False):

		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading KissManga Items")

		ret = []
		cnt = 1
		while 1:


			try:
				pages = self.getUpdatedSeries(self.seriesBase.format(num=cnt))
			except ValueError:
				break


			if not pages:
				break

			for page in pages:
				ret.append(page)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

			if not historical:
				break
			else:
				if cnt > 100:
					break

			cnt += 1

		self.log.info("Found %s total items", len(ret))
		return ret

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

		titleA = soup.find("a", class_='bigChar')
		return {"series_name": titleA.get_text()}

	def getChaptersFromSeriesPage(self, soup):
		table = soup.find('table', class_='listing')

		items = []
		for row in table.find_all("tr"):
			if not row.a:
				continue  # Skip the table header row

			chapter, date = row.find_all("td")
			item = {}
			item["origin_name"]  = chapter.get_text().strip()
			item["source_id"]    = urllib.parse.urljoin(self.urlBase, chapter.a['href'])
			item['posted_at']    = dateutil.parser.parse(date.get_text().strip())
			item["last_checked"] = datetime.datetime.now()

			items.append(item)


		return items

	def getChapterLinkFromSeriesPage(self, seriesUrl, historical=False):
		ret = []

		if " " in seriesUrl:
			seriesUrl = seriesUrl.replace(" ", "%20")
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

	def get_feed(self, historical=False):
		toScan = self.getUpdatedSeriesPages(historical)

		ret = []

		for url in toScan:
			try:
				items = self.getChapterLinkFromSeriesPage(url)
				for item in items:
					if item in ret:
						self.log.warn("Duplicate items in ret?")
						# raise ValueError("Duplicate items in ret?")
					else:
						ret.append(item)
				self._process_links_into_db(ret)
				ret = []
			except urllib.error.URLError:
				pass

		return ret

	def setup(self):
		cf_ok = self.wg.stepThroughJsWaf("http://kissmanga.com/", titleContains='Read manga online in high quality')
		self.log.info("CF Access return value: %s", cf_ok)
		if not cf_ok:
			raise ValueError("Could not access site due to cloudflare protection.")



if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		fl = FeedLoader()
		# fl.setup()
		# fl.getChapterLinkFromSeriesPage("http://kissmanga.com/Manga/Kuro-senpai-to-Kuroyashiki-no-Yami-ni-Mayowanai")
		fl.do_fetch_feeds(historical=False)
		# fl.go(historical=True)
		# fl.getSeriesUrls()

		# fl.getAllItems()

