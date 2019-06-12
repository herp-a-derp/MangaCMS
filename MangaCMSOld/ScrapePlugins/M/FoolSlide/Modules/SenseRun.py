
import runStatus
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase
import MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase


import MangaCMS.ScrapePlugins.RunBase
import settings
import time

class ContentLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideDownloadBase.FoolContentLoader):


	loggerPath = "Main.Manga.Se.Cl"
	pluginName = "Sense Scans Content Retreiver"
	tableKey = "se"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"
	groupName = "SenseScans"


	retreivalThreads = 1

	contentSelector = ('article', 'content')


class FeedLoader(MangaCMSOld.ScrapePlugins.M.FoolSlide.FoolSlideFetchBase.FoolFeedLoader):


	loggerPath = "Main.Manga.Se.Fl"
	pluginName = "Sense Scans Link Retreiver"
	tableKey = "se"
	dbName = settings.DATABASE_DB_NAME
	tableName = "MangaItems"



	urlBase = "http://reader.sensescans.com/"
	feedUrl = urlBase+"latest/{num}/"


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Se.Run"

	pluginName = "SenseLoader"

	sourceName = "Sense Scans"

	feedLoader = FeedLoader
	contentLoader = ContentLoader

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		fl = Runner()

		fl.go()

