

import traceback

import datetime
import urllib.parse
import dateutil.parser

import concurrent.futures

import MangaCMS.ScrapePlugins.LoaderBase
class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.NHentai.Fl"
	plugin_name = "NHentai Link Retreiver"
	plugin_key  = "nh"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "http://nhentai.net/"
	urlFeed = "http://nhentai.net/language/english/?page={num}"


	tableName = "HentaiItems"


	def getCategoryTags(self, soup):
		tagChunks = soup.find_all('div', class_='field-name')
		tags = []
		category = "None"

		# 'Origin'       : '',  (Category)
		for chunk in tagChunks:
			for rawTag in chunk.find_all("a", class_='tag'):
				if rawTag.span:
					rawTag.span.decompose()
				tag = rawTag.get_text().strip()

				if "Artist" in chunk.contents[0]:
					category = "Artist-"+tag.title()
					tag = "artist "+tag
				tag = tag.replace("  ", " ")
				tag = tag.replace(" ", "-")
				tags.append(tag)

		return category, tags

	def getUploadTime(self, soup):
		timeTag = soup.find("time")
		if not timeTag:
			raise ValueError("No time tag found!")

		ulDate = dateutil.parser.parse(timeTag['datetime']).replace(tzinfo=None)

		# No future times!
		if ulDate > datetime.datetime.now():
			self.log.warning("Clamping timestamp to now!")
			ulDate = datetime.datetime.now()
		return ulDate


	def getInfo(self, itemUrl):
		ret = {}
		soup = self.wg.getSoup(itemUrl)

		ret["series_name"], ret['tags'] = self.getCategoryTags(soup)
		ret['posted_at'] = self.getUploadTime(soup)

		return ret


	def parseItem(self, containerDiv, retag=False):
		item_url = urllib.parse.urljoin(self.urlBase, containerDiv.a["href"])

		# Do not decend into items where we've already added the item to the DB
		with self.row_context(url=item_url) as row:
			if row and not retag:
				return

		ret = {
			'source_id' : item_url
		}
		ret.update(self.getInfo(item_url))

		if not self.wanted_from_tags(ret['tags']):
			return None

		titleTd = containerDiv.find("div", class_='caption')
		ret['origin_name'] = titleTd.get_text().strip()

		return ret


	def update_item_tags(self, item):
		if not item['tags']:
			self.log.warning("Item has no tags '%s'?", item)
			return

		if not item['source_id']:
			self.log.warning("SourceID is empty: '%s'?", item)
			return


		self.log.info("Doing tag update.")
		# Do not decend into items where we've already added the item to the DB
		with self.row_context(url=item['source_id']) as row:
			if not row:
				self.log.error("No row for item! What'%s', %s.", item, row)
				return
			self.log.info("Updating %s", row)
			self.update_tags(row=row, tags=item['tags'])

	def loadFeedContent(self, pageOverride=None):
		self.log.info("Retrieving feed content...",)
		if not pageOverride:
			pageOverride = 1
		try:
			pageUrl = self.urlFeed.format(num=pageOverride)
			soup = self.wg.getSoup(pageUrl)
		except urllib.error.URLError:
			self.log.critical("Could not get page from NHentai!")
			self.log.critical(traceback.format_exc())
			return None

		return soup

	def get_feed(self, pageOverride=None, retag=False):
		# for item in items:
		# 	self.log.info(item)
		#

		soup = self.loadFeedContent(pageOverride)

		mainDiv = soup.find("div", class_="index-container")

		divs = mainDiv.find_all("div", class_='gallery')

		ret = []
		for itemDiv in divs:

			item = self.parseItem(itemDiv, retag)
			if item:
				ret.append(item)

			if retag and item:
				self.update_item_tags(item)

		return ret



def process(runner, pageOverride, retag=False):
	print("Executing with page offset: pageOverride")
	res = runner.getFeed(pageOverride=pageOverride, retag=retag)
	print("Received %s results!" % len(res))
	runner._processLinksIntoDB(res)



def getHistory(retag=False):


	print("Getting history")
	run = DbLoader()
	# with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
	# 	futures = [executor.submit(process, runner=run, pageOverride=x, retag=retag) for x in range(0, 1500)]
	# 	print("Waiting for executor to finish.")
	# 	executor.shutdown()



	for x in range(0, 1500):
		dat = run.get_feed(pageOverride=x, retag=True)
		run._process_links_into_db(dat)


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		getHistory()
		# run = DbLoader()
		# run.do_fetch_feeds()


