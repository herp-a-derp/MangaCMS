

from .DbLoader      import DbLoader
from .ContentLoader import ContentLoader

import MangaCMS.ScrapePlugins.RunBase

import time

import runStatus


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Books.Mk.Run"

	pluginName = "MkBookLoader"


	sourceName = "MadokamiBooks"
	feedLoader = DbLoader
	contentLoader = ContentLoader

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()
