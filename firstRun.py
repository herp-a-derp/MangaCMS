

'''
Do the initial database setup, so a functional system can be bootstrapped from an empty database.
'''

import MangaCMSOld.ScrapePlugins.M.BuMonitor.MonitorRun
import MangaCMSOld.ScrapePlugins.M.BuMonitor.ChangeMonitor



'''
We need one instance of each type of plugin (series, manga, hentai), plus some extra for no particular reason (safety!)

Each plugin is instantiated, and then the plugin database setup method is called.

'''
toInit = [
	MangaCMSOld.ScrapePlugins.M.BuMonitor.MonitorRun.BuWatchMonitor,
	MangaCMSOld.ScrapePlugins.M.BuMonitor.ChangeMonitor.BuDateUpdater,
	]


def checkInitTables():
	for plg in toInit:
		print(plg)
		tmp = plg()
		tmp.checkInitPrimaryDb()
		if hasattr(tmp, "checkInitSeriesDb"):
			tmp.checkInitSeriesDb()

if __name__ == "__main__":
	import MangaCMSOld.lib.logSetup
	MangaCMSOld.lib.logSetup.initLogging()
	checkInitTables()
