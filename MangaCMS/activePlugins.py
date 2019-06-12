
# pylint: disable=C0413
# Disable the import ordering crap, because we need to do the log setup
# first, as some of the plugins may have side effects (also, fix that)
if __name__ == "__main__":
	import MangaCMSOld.lib.logSetup
	MangaCMSOld.lib.logSetup.initLogging()

import MangaCMSOld.ScrapePlugins.M.BuMonitor.Run
import MangaCMSOld.ScrapePlugins.M.BuMonitor.Rescan



import MangaCMSOld.ScrapePlugins.M.Crunchyroll.Run
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.BotRunner
import MangaCMSOld.ScrapePlugins.M.IrcGrabber.IrcEnqueueRun
import MangaCMS.ScrapePlugins.M.Kawaii.Run
import MangaCMSOld.ScrapePlugins.M.MangaBox.Run
import MangaCMS.ScrapePlugins.M.MangaHere.Run
import MangaCMS.ScrapePlugins.M.MerakiScans.Run
import MangaCMSOld.ScrapePlugins.M.WebtoonLoader.Run            # Yeah. There is webtoon.com. and WebtoonsReader.com. Confusing much?
import MangaCMSOld.ScrapePlugins.M.ZenonLoader.Run

import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.DokiRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.RoseliaRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.S2Run
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.SenseRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun
import MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.VortexRun


import MangaCMS.ScrapePlugins.M.MangaStreamLoader.Run
import MangaCMS.ScrapePlugins.M.DynastyLoader.Run
import MangaCMS.ScrapePlugins.M.MangaDex.Run
import MangaCMS.ScrapePlugins.M.MangaZuki.Run
import MangaCMS.ScrapePlugins.M.McLoader.Run
import MangaCMS.ScrapePlugins.M.KissLoader.Run

import MangaCMS.ScrapePlugins.M.YoMangaLoader.Run
import MangaCMS.ScrapePlugins.M.MangaMadokami.Run

import MangaCMS.ScrapePlugins.H.SadPandaLoader.Run
import MangaCMS.ScrapePlugins.H.DjMoeLoader.Run
import MangaCMS.ScrapePlugins.H.PururinLoader.Run
import MangaCMS.ScrapePlugins.H.TsuminoLoader.Run
import MangaCMS.ScrapePlugins.H.Hentai2Read.Run
import MangaCMS.ScrapePlugins.H.DoujinOnlineLoader.Run
import MangaCMS.ScrapePlugins.H.ASMHentaiLoader.Run
import MangaCMS.ScrapePlugins.H.HitomiLoader.Run
import MangaCMS.ScrapePlugins.H.NHentaiLoader.Run
import MangaCMS.ScrapePlugins.H.HBrowseLoader.Run
import MangaCMS.ScrapePlugins.B.BooksMadokami.Run

# Convenience functions to make intervals clearer.
def days(num):
	return 60*60*24*num
def hours(num):
	return 60*60*num
def minutes(num):
	return 60*num

# Plugins in this dictionary are the active plugins. Comment out a plugin to disable it.
# plugin keys specify when plugins will start, and cannot be duplicates.
# All they do is specify the order in which plugins
# are run, initially, starting after 1-minue*{key} intervals
scrapePlugins = {
	2   : (MangaCMSOld.ScrapePlugins.M.BuMonitor.Run,                       hours( 1)),
	3   : (MangaCMSOld.ScrapePlugins.M.BuMonitor.Rescan,                    days(  7)),

	11  : (MangaCMS.ScrapePlugins.M.McLoader.Run,                        hours(12)),  # every 12 hours, it's just a single scanlator site.
	# 12  : (MangaCMSOld.ScrapePlugins.M.IrcGrabber.IrcEnqueueRun,            hours(12)),  # Queue up new items from IRC bots.
	# 15  : (MangaCMSOld.ScrapePlugins.M.IrcGrabber.BotRunner,                hours( 1)),  # Irc bot never returns. It runs while the app is live. Rerun interval doesn't matter, as a result.
	16  : (MangaCMS.ScrapePlugins.M.MangaHere.Run,                       hours(12)),
	17  : (MangaCMSOld.ScrapePlugins.M.WebtoonLoader.Run,                   hours( 8)),
	18  : (MangaCMS.ScrapePlugins.M.DynastyLoader.Run,                      hours( 8)),
	#19  : (MangaCMS.ScrapePlugins.M.KissLoader.Run,                      hours( 1)),
	20  : (MangaCMSOld.ScrapePlugins.M.Crunchyroll.Run,                     hours( 4)),
	22  : (MangaCMS.ScrapePlugins.M.Kawaii.Run,                          hours(12)),
	23  : (MangaCMSOld.ScrapePlugins.M.ZenonLoader.Run,                     hours(24)),
	24  : (MangaCMSOld.ScrapePlugins.M.MangaBox.Run,                        hours(12)),
	27  : (MangaCMS.ScrapePlugins.M.MerakiScans.Run,                     hours(12)),
	28  : (MangaCMS.ScrapePlugins.M.MangaZuki.Run,                          hours(12)),


	# FoolSlide modules

	61 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun,      hours(12)),
	62 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun,      hours(12)),
	63 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.DokiRun,            hours(12)),
	64 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun,       hours(12)),
	65 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun, hours(12)),
	# 66 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.JaptemMangaRun,     hours(12)),
	67 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun,      hours(12)),
	# 68 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.RoseliaRun,         hours(12)),
	69 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.S2Run,              hours(12)),
	70 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.SenseRun,           hours(12)),
	71 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun,     hours(12)),
	72 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun,     hours(12)),
	73 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun,      hours(12)),
	74 : (MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.VortexRun,          hours(12)),


	81 : (MangaCMS.ScrapePlugins.B.BooksMadokami.Run,                    hours(4)),
	#
	0   : (MangaCMS.ScrapePlugins.M.MangaDex.Run,                        hours( 6)),
	1   : (MangaCMS.ScrapePlugins.M.MangaStreamLoader.Run,               hours( 6)),
	25  : (MangaCMS.ScrapePlugins.M.YoMangaLoader.Run,                   hours(12)),
	80  : (MangaCMS.ScrapePlugins.M.MangaMadokami.Run,                    hours(4)),

	41  : (MangaCMS.ScrapePlugins.H.HBrowseLoader.Run,                   hours( 2)),
	42  : (MangaCMS.ScrapePlugins.H.PururinLoader.Run,                   hours( 2)),
	44  : (MangaCMS.ScrapePlugins.H.NHentaiLoader.Run,                   hours( 2)),
	45  : (MangaCMS.ScrapePlugins.H.SadPandaLoader.Run,                  hours(24)),
	46  : (MangaCMS.ScrapePlugins.H.DjMoeLoader.Run,                     hours( 2)),
	47  : (MangaCMS.ScrapePlugins.H.HitomiLoader.Run,                    hours( 2)),
	48  : (MangaCMS.ScrapePlugins.H.ASMHentaiLoader.Run,                 hours( 2)),
	49  : (MangaCMS.ScrapePlugins.H.Hentai2Read.Run,                     hours( 2)),
	50  : (MangaCMS.ScrapePlugins.H.DoujinOnlineLoader.Run,              hours( 2)),
	51  : (MangaCMS.ScrapePlugins.H.TsuminoLoader.Run,                   hours( 2)),

}




def get_plugins():
	ret = {}
	runner_map = {}
	for plugin_module, dummy_interval in scrapePlugins.values():
		plugin = plugin_module.Runner
		print("plugin.pluginName: ", plugin.pluginName)
		# print(dir(plugin))
		if not hasattr(plugin, 'pluginName'):
			print("No pluginName: ", plugin)
			continue

		if not hasattr(plugin, 'feedLoader'):
			print("No feedLoader: ", plugin)
			continue
		if not hasattr(plugin, 'contentLoader'):
			print("No contentLoader: ", plugin)
			continue

		if hasattr(plugin.feedLoader, 'tableKey'):
			pass
		elif hasattr(plugin.feedLoader, 'plugin_key'):
			print("Has plugin_key")
			plugin.feedLoader.tableKey = plugin.feedLoader.plugin_key
		else:
			print("No tableKey in feedLoader: ", plugin.feedLoader, hasattr(plugin.feedLoader, 'plugin_key'))
			continue

		if plugin.feedLoader.tableKey != "mk":
			assert plugin.feedLoader.tableKey not in ret, "Duplicate keys? Key: %s, for %s, matches %s" % (
				plugin.feedLoader.tableKey, plugin, ret[plugin.feedLoader.tableKey]['name'])

		item = {
			'feedLoader'    : plugin.feedLoader,
			'contentLoader' : plugin.contentLoader,
			'runner'        : plugin,
			'name'          : plugin.pluginName,
			"is_h"          : ".H." in plugin_module.__name__,
			"key"           : plugin.feedLoader.tableKey,
		}
		ret[plugin.feedLoader.tableKey]    = item
		runner_map[plugin_module.__name__] = item
	return ret, runner_map


PLUGIN_MAP, RUNNER_MAP = get_plugins()


if __name__ == "__main__":

	# scrapePlugins = {
		# 0 : (TextScrape.BakaTsuki.Run,                       60*60*24*7),  # Every 7 days, because books is slow to update
		# 1 : (TextScrape.JapTem.Run,                          60*60*24*5),
		# 3 : (TextScrape.Guhehe.Run,                          60*60*24*5),
		# 2 : (TextScrape.ReTranslations.Run,                  60*60*24*1)   # There's not much to actually scrape here, and it's google, so I don't mind hitting their servers a bit.
	# }

	run = [
				# MangaCMS.ScrapePlugins.M.MangaMadokami.Run,

				# MangaCMSOld.ScrapePlugins.M.Crunchyroll.Run,
				# MangaCMS.ScrapePlugins.M.DynastyLoader.Run,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.CanisMajorRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ChibiMangaRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.DokiRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.GoMangaCoRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.IlluminatiMangaRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.MangatopiaRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.S2Run,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.SenseRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.ShoujoSenseRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TripleSevenRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.TwistedHelRun,
				# MangaCMSOld.ScrapePlugins.M.FoolSlide.Modules.VortexRun,
				# MangaCMS.ScrapePlugins.M.Kawaii.Run,
				# MangaCMSOld.ScrapePlugins.M.MangaBox.Run,
				# MangaCMS.ScrapePlugins.M.MangaDex.Run,
				# MangaCMS.ScrapePlugins.M.MangaHere.Run,
				# MangaCMS.ScrapePlugins.M.MangaStreamLoader.Run,
				# MangaCMS.ScrapePlugins.M.MangaZuki.Run,
				# MangaCMS.ScrapePlugins.M.McLoader.Run,
				# MangaCMS.ScrapePlugins.M.MerakiScans.Run,
				# MangaCMSOld.ScrapePlugins.M.WebtoonLoader.Run,
				# MangaCMS.ScrapePlugins.M.YoMangaLoader.Run,
				# MangaCMSOld.ScrapePlugins.M.ZenonLoader.Run,
				# MangaCMSOld.ScrapePlugins.M.BuMonitor.Rescan,
				# MangaCMSOld.ScrapePlugins.M.BuMonitor.Run,

				# MangaCMSOld.ScrapePlugins.B.BooksMadokami.Run,


				MangaCMS.ScrapePlugins.H.ASMHentaiLoader.Run,
				MangaCMS.ScrapePlugins.H.DjMoeLoader.Run,
				MangaCMS.ScrapePlugins.H.DoujinOnlineLoader.Run,
				MangaCMS.ScrapePlugins.H.HBrowseLoader.Run,
				MangaCMS.ScrapePlugins.H.Hentai2Read.Run,
				MangaCMS.ScrapePlugins.H.HitomiLoader.Run,
				MangaCMS.ScrapePlugins.H.NHentaiLoader.Run,
				MangaCMS.ScrapePlugins.H.PururinLoader.Run,
				MangaCMS.ScrapePlugins.H.TsuminoLoader.Run,
				# MangaCMS.ScrapePlugins.H.SadPandaLoader.Run,
		]

	print("Test run!")
	import nameTools as nt

	def callGoOnClass(passedModule):
		print("Passed module = ", passedModule)
		print("Calling class = ", passedModule.Runner)
		instance = passedModule.Runner()
		instance.go()
		print("Instance:", instance)


	nt.dirNameProxy.startDirObservers()
	import signal
	import runStatus

	def signal_handler(dummy_signal, dummy_frame):
		if runStatus.run:
			runStatus.run = False
			print("Telling threads to stop (activePlugins)")
		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt


	signal.signal(signal.SIGINT, signal_handler)
	import sys
	import traceback
	print("Starting")
	try:
		if len(sys.argv) > 1 and int(sys.argv[1]) in scrapePlugins:
			plugin, interval = scrapePlugins[int(sys.argv[1])]
			print(plugin, interval)
			callGoOnClass(plugin)
		else:

			print("Loopin!", scrapePlugins)
			for plugin in run:
				print(plugin)
				try:
					callGoOnClass(plugin)
				except Exception:
					print()
					print("Wat?")
					traceback.print_exc()
					# raise
					print("Continuing on with next source.")

	except:
		traceback.print_exc()


	print("Complete")

	nt.dirNameProxy.stop()
	sys.exit()
