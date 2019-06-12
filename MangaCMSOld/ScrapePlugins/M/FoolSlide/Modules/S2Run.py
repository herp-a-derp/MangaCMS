

import runStatus
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import MangaCMS.ScrapePlugins.RunBase
import settings
import time


class ContentLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):



	loggerPath = "Main.Manga.S2.Cl"
	pluginName = "S2 Scans Content Retreiver"
	tableKey = "s2"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "S2Scans"


	retreivalThreads = 2

	contentSelector = ('article', 'content')


class FeedLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):

	loggerPath = "Main.Manga.S2.Fl"
	pluginName = "S2 Scans Link Retreiver"
	tableKey = "s2"
	dbName = settings.DATABASE_DB_NAME


	tableName = "MangaItems"

	urlBase = "http://reader.s2smanga.com/"
	feedUrl = "http://reader.s2smanga.com/directory/{num}/"

class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.S2.Run"

	pluginName = "S2Loader"

	sourceName = "S2 Scans"

	feedLoader = FeedLoader
	contentLoader = ContentLoader


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

