
import runStatus
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import MangaCMS.ScrapePlugins.RunBase
import settings
import time

class FeedLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.MngTop.Cl"
	pluginName = "Mangatopia Content Retreiver"
	tableKey = "mp"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "Mangatopia"



	urlBase = "http://mangatopia.net/slide/"
	feedUrl = urlBase+"latest/{num}/"


	def filterItem(self, item):
		if "/es/" in item['sourceUrl']:
			return False

		if "[EN]" in item['seriesName']:
			item['seriesName'] = item['seriesName'].replace("[EN]", "").strip()

		return item


class ContentLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.MngTop.Cl"
	pluginName = "Mangatopia Content Retreiver"
	tableKey = "mp"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "Mangatopia"


	retreivalThreads = 1

	contentSelector = ('article', 'content')



class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MngTop.Run"

	pluginName = "MangatopiaLoader"


	sourceName = "Mangatopia"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

