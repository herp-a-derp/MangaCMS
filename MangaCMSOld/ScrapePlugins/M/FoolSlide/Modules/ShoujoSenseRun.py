

import runStatus
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import MangaCMS.ScrapePlugins.RunBase
import settings
import time

class FeedLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Manga.Sj.Fl"
	pluginName = "Shoujo Sense Scans Link Retreiver"
	tableKey = "sj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"



	urlBase = "http://reader.shoujosense.com/"
	feedUrl = urlBase+"latest/{num}/"

class ContentLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):


	loggerPath = "Main.Manga.Sj.Cl"
	pluginName = "Shoujo Sense Scans Content Retreiver"
	tableKey = "sj"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "ShoujoSense"


	retreivalThreads = 1

	contentSelector = ('article', 'content')

class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Sj.Run"

	pluginName = "ShoujoSense"


	sourceName = "ShoujoSense"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

