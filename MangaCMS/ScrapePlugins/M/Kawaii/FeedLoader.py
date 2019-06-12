
import datetime

import runStatus
import MangaCMS.ScrapePlugins.LoaderBase

# Only downlad items in language specified.
# Set to None to disable filtering (e.g. fetch ALL THE FILES).
DOWNLOAD_ONLY_LANGUAGE = "English"

class FeedLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):



	logger_path = "Main.Manga.Kw.Fl"
	plugin_name = "Kawaii-Scans Link Retreiver"
	plugin_key  = "kw"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	urlBase = "http://kawaii.ca/"
	feedUrl = "http://kawaii.ca/reader/"

	def getItemPages(self, url, title):
		# print("Should get item for ", url)

		soup = self.wg.getSoup(url)
		ret = []

		pager = soup.find("div", class_="pager")
		spans = pager.find_all('span')
		if len(spans) != 3:
			self.log.error("Invalid span items! Page: '%s'", url)
			return ret

		dummy_series, chapter, dummy_page = spans

		# First string in the tag should be "Chapter".
		assert 'Chapter' in list(chapter.stripped_strings)[0]


		for option in chapter.find_all("option"):
			item = {}

			chapUrl = '{series}/{chapter}'.format(series=url, chapter=option['value'])
			chapTitle = option.get_text()


			item["origin_name"] = "{series} - {file}".format(series=title, file=chapTitle)
			item["source_id"]   = chapUrl
			item["series_name"] = title

			# There is no upload date information
			item["posted_at"] = datetime.datetime.now()


			ret.append(item)

		return ret



	def getSeriesUrls(self):
		ret = []
		print("wat?")
		soup = self.wg.getSoup(self.feedUrl)
		div = soup.find("div", class_="pager")
		for option in div.find_all('option'):
			if option['value'] == '0':
				continue
			url = 'http://kawaii.ca/reader/{manga}'.format(manga=option['value'])
			ret.append((url, option.get_text()))

		return ret

	def get_feed(self):

		self.log.info( "Loading Mc Items")

		ret = []

		seriesPages = self.getSeriesUrls()


		for url, title in seriesPages:

			itemList = self.getItemPages(url, title)
			for item in itemList:
				ret.append(item)

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				break
		self.log.info("Found %s total items", len(ret))
		return ret




if __name__ == "__main__":
	print('wat')

	import utilities.testBase as tb

	with tb.testSetup(load=False):
		cl = FeedLoader()
		cl.do_fetch_feeds()
