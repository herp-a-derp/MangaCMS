
import time
import abc
import zipfile
import traceback
import magic
import mimetypes
import os.path
from concurrent.futures import ThreadPoolExecutor

import runStatus
import settings
import WebRequest
import MangaCMSOld.ScrapePlugins.MangaScraperDbBase
import nameTools as nt

import MangaCMSOld.ScrapePlugins.ScrapeExceptions as ScrapeExceptions

class RetreivalBase(MangaCMSOld.ScrapePlugins.MangaScraperDbBase.MangaScraperDbBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	pluginType = "ContentRetreiver"

	itemLimit = 250
	retreivalThreads = 1

	def __init__(self, *args, **kwargs):
		self.die = False
		self.wg = WebRequest.WebGetRobust(logPath=self.loggerPath+".Web")

		super().__init__(*args, **kwargs)



	@abc.abstractmethod
	def getLink(self, link):
		pass

	# Provision for a delay. If checkDelay returns false, item is not enqueued
	def checkDelay(self, inTime):
		return True

	# And for logging in (if needed)
	def setup(self):
		pass

	def _retreiveTodoLinksFromDB(self):

		# self.QUERY_DEBUG = True

		self.log.info( "Fetching items from db...",)

		rows = self.getRowsByValue(dlState=0)

		self.log.info( "Done")

		items = []
		for item in rows:

			if self.checkDelay(item["retreivalTime"]):
				item["retreivalTime"] = time.gmtime(item["retreivalTime"])
				items.append(item)

		self.log.info( "Have %s new items to retreive in %sDownloader", len(items), self.tableKey.title())



		items = sorted(items, key=lambda k: k["retreivalTime"], reverse=True)
		if self.itemLimit:
			items = items[:self.itemLimit]

		return items


	def _fetchLink(self, link):
		try:
			if link is None:
				self.log.error("Worker received null task! Wat?")
				return
			if self.die:
				self.log.warning("Skipping job due to die flag!")
				return
			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				return

			status = self.getLink(link)

			ret1 = None
			if status == 'phash-duplicate':
				ret1 = self.mon_con.incr('phash_dup_items', 1)
			elif status == 'binary-duplicate':
				ret1 = self.mon_con.incr('bin_dup_items', 1)

			# We /always/ send the "fetched_items" count entry.
			# However, the deduped result is only send if the item is actually deduped.
			ret2 = self.mon_con.incr('fetched_items', 1)
			self.log.info("Retreival complete. Sending log results:")
			if ret1:
				self.log.info("	-> %s", ret1)
			self.log.info("	-> %s", ret2)

		except SystemExit:
			self.die = True
			raise

		except ScrapeExceptions.LimitedException as e:
			self.log.info("Remote site is rate limiting. Exiting early.")
			self.die = True
			raise e

		except KeyboardInterrupt:
			self.log.critical("Keyboard Interrupt!")
			self.log.critical(traceback.format_exc())

			# Reset the download, since failing because a keyboard interrupt is not a remote issue.
			self.updateDbEntry(link["sourceUrl"], dlState=0)
			raise

		except Exception:
			ret = self.mon_con.incr('failed_items', 1)
			self.log.critical("Sending log result: %s", ret)

			self.log.critical("Exception!")
			traceback.print_exc()
			self.log.critical(traceback.format_exc())



	def processTodoLinks(self, links):
		if links:

			with ThreadPoolExecutor(max_workers=self.retreivalThreads) as executor:

				futures = [executor.submit(self._fetchLink, link) for link in links]

				while futures:
					futures = [tmp for tmp in futures if not (tmp.done() or tmp.cancelled())]
					if not runStatus.run:
						self.log.warning("Cancelling all pending futures")
						for job in futures:
							job.cancel()
						self.log.warning("Jobs cancelled. Exiting executor context.")
						return
					time.sleep(1)





	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Filesystem stuff
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	# either locate or create a directory for `seriesName`.
	# If the directory cannot be found, one will be created.
	# Returns {pathToDirectory string}, {HadToCreateDirectory bool}
	def locateOrCreateDirectoryForSeries(self, seriesName):

		if self.shouldCanonize:
			canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		else:
			canonSeriesName = seriesName

		safeBaseName = nt.makeFilenameSafe(canonSeriesName)


		if canonSeriesName in nt.dirNameProxy:
			self.log.info("Have target dir for '%s' Dir = '%s'", canonSeriesName, nt.dirNameProxy[canonSeriesName]['fqPath'])
			return nt.dirNameProxy[canonSeriesName]["fqPath"], False
		else:
			self.log.info("Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			targetDir = os.path.join(settings.baseDir, safeBaseName)
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
					return targetDir, True

				except FileExistsError:
					# Probably means the directory was concurrently created by another thread in the background?
					self.log.critical("Directory doesn't exist, and yet it does?")
					self.log.critical(traceback.format_exc())
					pass
				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())

			else:
				self.log.warning("Directory not found in dir-dict, but it exists!")
				self.log.warning("Directory-Path: %s", targetDir)
				self.log.warning("Base series name: %s", seriesName)
				self.log.warning("Canonized series name: %s", canonSeriesName)
				self.log.warning("Safe canonized name: %s", safeBaseName)
			return targetDir, False

	def save_image_set(self, fqfilename, image_list):

		filepath, fileN = os.path.split(fqfilename)
		fileN = fileN.replace('.zip .zip', '.zip')
		fileN = fileN.replace('.zip.zip', '.zip')
		fileN = fileN.replace(' .zip', '.zip')
		fileN = fileN.replace('..zip', '.zip')
		fileN = nt.makeFilenameSafe(fileN)

		fqfilename = os.path.join(filepath, fileN)
		fqfilename = self.insertCountIfFilenameExists(fqfilename)
		self.log.info("Complete filepath: %s", fqfilename)

		assert len(image_list) >= 1
		chop = len(fileN)-4

		while 1:
			try:
				arch = zipfile.ZipFile(fqfilename, "w")

				#Write all downloaded files to the archive.
				for imageName, imageContent in image_list:
					assert isinstance(imageName, str)
					assert isinstance(imageContent, bytes)

					mtype = magic.from_buffer(imageContent, mime=True)
					assert "image" in mtype.lower()

					_, ext = os.path.splitext(imageName)
					if not ext:
						self.log.warning("Missing extension in archive file: %s", imageName)
						fext = mimetypes.guess_extension(mtype)
						self.log.warning("Appending guessed file-extension %s", fext)
						imageName += fext

					arch.writestr(imageName, imageContent)
				arch.close()
				return fqfilename

			except (IOError, OSError):
				chop = chop - 1
				filepath, fileN = os.path.split(fqfilename)

				fileN = fileN[:chop]+fileN[-4:]
				self.log.warn("Truncating file length to %s characters and re-encoding.", chop)
				fileN = fileN.encode('utf-8','ignore').decode('utf-8')
				fileN = nt.makeFilenameSafe(fileN)
				fqfilename = os.path.join(filepath, fileN)
				fqfilename = self.insertCountIfFilenameExists(fqfilename)




	def insertCountIfFilenameExists(self, fqFName):

		base, ext = os.path.splitext(fqFName)
		loop = 1
		while os.path.exists(fqFName):
			fqFName = "%s - (%d).%s" % (base, loop, ext)
			loop += 1

		return fqFName

	def do_fetch_content(self):
		if hasattr(self, 'setup'):
			self.setup()

		todo = self._retreiveTodoLinksFromDB()
		if not runStatus.run:
			return

		if not todo:

			ret = self.mon_con.incr('fetched_items.count', 0)
			self.log.info("No links to fetch. Sending null result: %s", ret)

		if todo:
			self.processTodoLinks(todo)
		self.log.info("ContentRetreiver for %s has finished.", self.pluginName)

	def go(self):
		raise ValueError("use do_fetch_content() instead!")
