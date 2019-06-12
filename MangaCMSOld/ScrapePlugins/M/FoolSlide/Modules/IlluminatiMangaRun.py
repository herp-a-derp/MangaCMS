


import MangaCMS.ScrapePlugins.RunBase
import settings

import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase

import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase

import time
import runStatus

DB_KEY     = "im"
LONG_NAME  = "Illuminati Manga"
SHORT_NAME = "IM"
GROUP_NAME = "IlluminatiManga"

URL_BASE = "http://reader.manga-download.org/"
READER_POSTFIX = "latest/{num}/"

class FeedLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):



	loggerPath = "Main.Manga.%s.Fl" % SHORT_NAME
	pluginName = "%s Link Retreiver" % LONG_NAME
	tableKey = DB_KEY
	dbName = settings.DATABASE_DB_NAME


	tableName = "MangaItems"

	urlBase = URL_BASE
	feedUrl = urlBase+READER_POSTFIX



class ContentLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):




	loggerPath = "Main.Manga.%s.Cl" % SHORT_NAME
	pluginName = "%s Content Retreiver" % LONG_NAME
	tableKey = DB_KEY
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = GROUP_NAME


	retreivalThreads = 1

	contentSelector = ('article', 'content')

class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.%s.Run" % SHORT_NAME

	pluginName = "%sLoader" % GROUP_NAME

	sourceName = "%s" % GROUP_NAME

	feedLoader = FeedLoader
	contentLoader = ContentLoader

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

