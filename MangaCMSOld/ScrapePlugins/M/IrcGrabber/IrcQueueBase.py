



import time

import abc
import WebRequest
import MangaCMSOld.ScrapePlugins.MangaScraperDbBase

class IrcQueueBase(MangaCMSOld.ScrapePlugins.MangaScraperDbBase.MangaScraperDbBase):

	pluginType = "IrcSiteMonitor"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.wg = WebRequest.WebGetRobust(logPath=self.loggerPath+".Web")


	def processLinksIntoDB(self, itemDataSets, isPicked=False):

		self.log.info( "Inserting...",)
		newItems = 0

		with self.transaction() as cur:
			for itemKey, itemData in itemDataSets:

				if '[jp]' in itemData.lower():
					self.log.warning("Japanese langauge item. Skipping")
					continue

				if itemData is None:
					print("itemDataSets", itemDataSets)
					print("WAT")

				row = self.getRowsByValue(limitByKey=False, sourceUrl=itemKey, cur=cur)
				if not row:
					newItems += 1


					# Flags has to be an empty string, because the DB is annoying.
					#
					# TL;DR, comparing with LIKE in a column that has NULLs in it is somewhat broken.
					#
					self.insertIntoDb(retreivalTime = time.time(),
										sourceUrl   = itemKey,
										sourceId    = itemData,
										dlState     = 0,
										flags       = '',
										commit      = False,
										cur         = cur)

					self.log.info("New item: %s", itemData)


			self.log.info( "Done")

		return newItems


	def go(self):

		self._resetStuckItems()
		self.log.info("Getting feed items")

		feedItems = self.getMainItems()
		self.log.info("Processing feed Items")

		self.processLinksIntoDB(feedItems)
		self.log.info("Complete")





