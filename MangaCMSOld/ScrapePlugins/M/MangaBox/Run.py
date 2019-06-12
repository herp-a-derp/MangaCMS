
from .Loader import Loader

import MangaCMS.ScrapePlugins.RunBase

import time


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.Mbx.Run"

	pluginName = "MbxLoader"


	contentLoader = None
	feedLoader = None

	def _go(self):

		self.log.info("Checking Manga Box for updates")
		fl = Loader()
		fl.go()




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = Runner()
		run.go()

