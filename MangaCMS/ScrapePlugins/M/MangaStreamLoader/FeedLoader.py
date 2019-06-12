

import MangaCMS.lib.logSetup
import runStatus
if __name__ == "__main__":
	MangaCMS.lib.logSetup.initLogging()
	runStatus.preloadDicts = False




import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import datetime

import MangaCMS.ScrapePlugins.LoaderBase
import nameTools as nt

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):



	logger_path = "Main.Manga.Ms.Fl"
	plugin_name = "Mangastream.com Scans Link Retreiver"
	plugin_key  = "ms"
	is_manga    = True
	is_hentai   = False
	is_book     = False

	urlBase    = "http://mangastream.com/"
	seriesBase = "http://mangastream.com/manga"


	def extractItemInfo(self, soup):

		ret = {}
		main = soup.find('div', class_='col-sm-8')

		ret["title"] = main.h1.get_text().strip()

		return ret

	def getItemPages(self, pageUrl):
		self.log.info("Should get item for '%s'", pageUrl)

		ret = []

		soup = self.wg.getSoup(pageUrl)
		baseInfo = self.extractItemInfo(soup)

		table = soup.find('table', class_='table-striped')

		for row in table.find_all("tr"):

			if not row.td:
				continue
			if not row.a:
				continue
			chapter, ulDate = row.find_all('td')

			chapTitle = chapter.get_text().strip()

			# Fix stupid chapter naming
			chapTitle = chapTitle.replace("Ep. ", "c")

			reldate_str = ulDate.get_text().strip()
			if reldate_str == "Today":
				date = datetime.datetime.now()
			else:
				date = dateutil.parser.parse(reldate_str, fuzzy=True)

			item = {}

			url = row.a["href"]
			url = urllib.parse.urljoin(self.urlBase, url)

			item["origin_name"]    = "{series} - {file}".format(series=baseInfo["title"], file=chapTitle)
			item["source_id"]      = url
			item["series_name"]    = baseInfo["title"]
			item["posted_at"]      = date

			if not item in ret:
				ret.append(item)

		self.log.info("Found %s chapters for series '%s'", len(ret), baseInfo["title"])
		return ret



	def getSeriesUrls(self):
		ret = set()

		soup = self.wg.getSoup(self.seriesBase)
		table = soup.find('table', class_='table-striped')

		rows = table.find_all("tr")


		for row in rows:
			if not row.td:
				continue
			series, dummy_chapName = row.find_all('td')
			if not series.a:
				continue

			item_url = urllib.parse.urljoin(self.urlBase, series.a['href'])
			ret.add(item_url)

		self.log.info("Found %s series", len(ret))

		return ret


	def get_feed(self, historical=False):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Red Hawk Items")


		seriesPages = self.getSeriesUrls()

		tot = 0

		for item in seriesPages:
			ret = []

			itemList = self.getItemPages(item)
			for item in itemList:
				ret.append(item)
				tot += 1

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break

			self._process_links_into_db(ret)

		self.log.info("Found %s total items", tot)
		return []


if __name__ == '__main__':
	fl = FeedLoader()
	print("fl", fl)
	fl.do_fetch_feeds()
	# fl.getSeriesUrls()
	# items = fl.getItemPages('http://mangastream.com/manga/area_d')
	# print("Items")
	# for item in items:
	# 	print("	", item)

