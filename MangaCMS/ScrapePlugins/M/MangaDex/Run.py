

import MangaCMS.ScrapePlugins.RunBase

from .FeedLoader import FeedLoader
from .ContentLoader import ContentLoader


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MDx.Run"

	pluginName = "MangaDexLoader"

	sourceName = "MangaDex"
	feedLoader = FeedLoader
	contentLoader = ContentLoader

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()

