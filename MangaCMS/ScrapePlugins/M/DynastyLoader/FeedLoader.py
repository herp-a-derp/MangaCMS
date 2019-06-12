

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

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):

	logger_path  = "Main.Manga.Dy.Fl"
	plugin_name  = "Dynasty Scans Link Retreiver"
	plugin_key   = "dy"
	is_manga    = True
	is_hentai   = False
	is_book     = False

	urlBase    = "http://dynasty-scans.com/"
	seriesBase = "http://dynasty-scans.com/?page={num}"

	def extractItemInfo(self, soup):

		ret = {}

		titleH = soup.find("h3", class_='subj')
		ret["title"] = titleH.get_text().strip()
		return ret


	def getItems(self, url):
		ret = []

		soup = self.wg.getSoup(url)

		if soup.find("div", class_='span8'):
			mainDiv = soup.find("div", class_='span8')
		elif soup.find("div", class_='chapters index'):
			mainDiv = soup.find("div", class_='chapters index')
		else:
			raise ValueError("Could not find item container?")


		curDate = None
		for child in mainDiv.find_all(True, recursive=False):  # Iterate over only tag children

			if child.name == 'h4':
				curDate = dateutil.parser.parse(child.string.strip())
			elif child.name == 'a':
				item = {}

				item["source_id"]     = urllib.parse.urljoin(self.urlBase, child['href'])
				item["posted_at"]     = curDate
				item["last_checked"]  = datetime.datetime.now()

				titleDiv = child.find("div", class_='title')

				title = titleDiv.contents[0].strip()
				if titleDiv.small:
					title += ' {%s}' % titleDiv.small.text.strip()

				item["origin_name"] = title

				tagDiv = child.find('div', class_='tags')
				if tagDiv:
					tags = tagDiv.find_all("span")
					tags = [tag.get_text().replace(" ", "-").replace(":", "").lower() for tag in tags]
					item["tags"] = tags

				ret.append(item)

			else:
				# Pagination stuff, etc...
				continue


		self.log.info("Found %s series", len(ret))

		return ret


	def get_feed(self, historical=False):
		# for item in items:
		# 	self.log.info( item)
		#

		self.log.info( "Loading Dynasty Scans Items")

		ret = []
		cnt = 1
		while 1:


			pages = self.getItems(self.seriesBase.format(num=cnt))


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
	# fl.do_fetch_feeds(historical=True)
	# fl.getSeriesUrls()
	# fl.getAllItems()
	# items = fl.getItemPages('http://www.webtoons.com/episodeList?titleNo=78')
	# print("Items")
	# for item in items:
	# 	print("	", item)

