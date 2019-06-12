

import MangaCMS.ScrapePlugins.RunBase

from .FeedLoader import FeedLoader
from .ContentLoader import ContentLoader


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mk.Run"

	pluginName = "MkLoader"

	sourceName = "MangaMadokami"
	feedLoader = FeedLoader
	contentLoader = ContentLoader

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()
