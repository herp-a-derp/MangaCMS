
import WebRequest
import settings
import os
import os.path

import nameTools as nt

import time
import random
import urllib.parse
import re
import sys
import runStatus
import traceback
import bs4
import datetime

import MangaCMS.ScrapePlugins.RetreivalBase
import MangaCMS.ScrapePlugins.RunBase

from concurrent.futures import ThreadPoolExecutor



HTTPS_CREDS = [
	("manga.madokami.al",         settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("http://manga.madokami.al",  settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]


class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):


	logger_path = "Main.Books.Mk.Cl"
	plugin_name = "Books.Madokami Content Retreiver"
	plugin_key = "bmk"

	is_manga    = False
	is_hentai   = False
	is_book     = True


	retreivalThreads = 1

	tableName = "BookItems"
	urlBase = "https://manga.madokami.al/"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.wg = WebRequest.WebGetRobust(creds=HTTPS_CREDS)


	def getLinkFile(self, fileUrl):

		scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(fileUrl)
		path = urllib.parse.quote(path)
		fileUrl = urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))

		pgctnt, pghandle = self.wg.getpage(fileUrl, returnMultiple = True, addlHeaders={'Referer': "https://manga.madokami.al"})
		pageUrl = pghandle.geturl()
		hName = urllib.parse.urlparse(pageUrl)[2].split("/")[-1]
		self.log.info( "HName: %s", hName, )
		self.log.info( "Size = %s", len(pgctnt))


		return pgctnt, hName



	def get_link(self, link_row_id):
		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup
			seriesName = row.series_name
			originName = row.origin_name
			source_url = row.source_id

			# Delete old (now invalid) rows
			if "manga.madokami.com" in source_url:
				self.log.warning("Row points to old madokami! Deleting!")
				row.tags.clear()
				sess.delete(row)

				return

		target_dir, new_dir = self.locateOrCreateDirectoryForSeries(seriesName)
		with self.row_context(dbid=link_row_id) as row:
			row.dirstate = 'created_dir' if new_dir else 'had_dir'

		sourceUrl, originFileName = source_url, originName

		self.log.info( "Should retreive: %s, url - %s", originFileName, sourceUrl)


		with self.row_context(dbid=link_row_id) as row:
			row.state = 'fetching'


		try:
			content, hName = self.getLinkFile(sourceUrl)
		except:
			self.log.error("Unrecoverable error retrieving content %s", (seriesName, originName, source_url))
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return

		hName = urllib.parse.unquote(hName)
		fName = "%s - %s" % (originFileName, hName)
		fqFName = os.path.join(target_dir, fName)

		# This call also inserts the file parameters into the row
		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup
			fqFName = self.save_archive(row, sess, fqFName, content)

		#self.log.info( filePath)

		with self.row_context(dbid=link_row_id) as row:
			row.state = 'processing'


		self.log.info( "Done")
		with self.row_context(dbid=link_row_id) as row:
			row.state = 'complete'
			row.downloaded_at = datetime.datetime.now()
			row.last_checked = datetime.datetime.now()

		return


	# either locate or create a directory for `seriesName`.
	# If the directory cannot be found, one will be created.
	# Returns {pathToDirectory string}, {HadToCreateDirectory bool}
	def locateOrCreateDirectoryForSeries(self, seriesName):

		if self.shouldCanonize and self.is_manga:
			canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		else:
			canonSeriesName = seriesName

		safeBaseName = nt.makeFilenameSafe(canonSeriesName)


		targetDir = os.path.join(settings.mkSettings["dirs"]['bookDir'], safeBaseName)
		if not os.path.exists(targetDir):
			self.log.info("Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			try:
				os.makedirs(targetDir)
				return targetDir, True

			except FileExistsError:
				# Probably means the directory was concurrently created by another thread in the background?
				self.log.critical("Directory doesn't exist, and yet it does?")
				self.log.critical(traceback.format_exc())
			except OSError:
				self.log.critical("Directory creation failed?")
				self.log.critical(traceback.format_exc())

		else:
			self.log.info("Directory exists.")
			self.log.info("Directory not found in dir-dict, but it exists!")
			self.log.info("Directory-Path: %s", targetDir)
			self.log.info("Base series name: %s", seriesName)
			self.log.info("Canonized series name: %s", canonSeriesName)
			self.log.info("Safe canonized name: %s", safeBaseName)
		return targetDir, False



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		run.do_fetch_content()


