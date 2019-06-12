
# XDCC Plugins

import MangaCMSOld.ScrapePlugins.M.IrcGrabber.IrcOfferLoader.IrcQueue
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.IMangaScans.ImsScrape
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.EgScans.EgScrape
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.IlluminatiManga.IrcQueue
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.SimpleXdccParser.IrcQueue
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.ModernXdccParser.IrcQueue
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.TextPackScraper.IrcQueue

# Trigger loader plugins
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.CatScans.IrcQueue
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.RenzokuseiScans.IrcQueue

# Channel grabber
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.ChannelLister.ChanLister

import MangaCMS.ScrapePlugins.RunBase

import time
import traceback
import runStatus


class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.IRC.Q.Run"

	pluginName = "IrcEnqueue"

	runClasses = [
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.IMangaScans.ImsScrape.IMSTriggerLoader,
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.EgScans.EgScrape.EgTriggerLoader,
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.ModernXdccParser.IrcQueue.TriggerLoader,
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.TextPackScraper.IrcQueue.TriggerLoader,
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.IlluminatiManga.IrcQueue.TriggerLoader,

		MangaCMSOld.ScrapePlugins.M.IrcGrabber.CatScans.IrcQueue.TriggerLoader,
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.RenzokuseiScans.IrcQueue.TriggerLoader,

		MangaCMSOld.ScrapePlugins.M.IrcGrabber.ChannelLister.ChanLister.ChannelTriggerLoader,

		MangaCMSOld.ScrapePlugins.M.IrcGrabber.SimpleXdccParser.IrcQueue.TriggerLoader,
		MangaCMSOld.ScrapePlugins.M.IrcGrabber.IrcOfferLoader.IrcQueue.TriggerLoader,
	]

	def _go(self):

		self.log.info("Checking IRC feeds for updates")

		for runClass in self.runClasses:

			try:
				fl = runClass()
				fl.go()
			except Exception as e:
				self.log.critical("Error in IRC enqueue system!")
				self.log.critical(traceback.format_exc())
				self.log.critical("Exception:")
				self.log.critical(e)
				self.log.critical("Continuing with next source")



			time.sleep(3)

			if not runStatus.run:
				return

if __name__ == "__main__":
	import MangaCMSOld.lib.logSetup
	MangaCMSOld.lib.logSetup.initLogging()
	run = Runner()
	run.go()


