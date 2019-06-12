

import MangaCMS.ScrapePlugins.RunBase

from .DbLoader import DbLoader
from .ContentLoader import ContentLoader

class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):


	loggerPath = "Main.Manga.DoujinOnline.Run"
	pluginName = "DoujinOnline"


	sourceName = "DoujinOnline"
	feedLoader = DbLoader
	contentLoader = ContentLoader





if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		mon = Runner()
		mon.go()

