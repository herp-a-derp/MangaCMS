

from .FeedLoader import FeedLoader
from .ContentLoader import ContentLoader

import MangaCMS.ScrapePlugins.RunBase

import time

import runStatus


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mp.Run"

	pluginName = "MpLoader"

	sourceName = "MangaPark"
	feedLoader = FeedLoader
	contentLoader = ContentLoader






if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		mon = Runner()
		mon.go()

