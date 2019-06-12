
from . import MonitorRun
from . import ChangeMonitor
import MangaCMS.ScrapePlugins.RunBase

class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):

	loggerPath = "Main.Manga.Bu.Run"
	pluginName = "BuMon"


	contentLoader = None
	feedLoader = None

	def _go(self):

		runner = MonitorRun.BuWatchMonitor()
		runner.go()

		chMon = ChangeMonitor.BuDateUpdater()
		chMon.go()



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():
		mon = Runner()
		mon.go()

