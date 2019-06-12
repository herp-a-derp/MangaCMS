
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

import MangaCMS.cleaner.processDownload


HTTPS_CREDS = [
	(        "manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	( "http://manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]


class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):


	logger_path = "Main.Manga.Mk.Cl"
	plugin_name = "Manga.Madokami Content Retreiver"
	plugin_key  = "mk"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	retreival_threads = 2

	urlBase = "https://manga.madokami.al/"

	itemLimit = 5000

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

		hName          = urllib.parse.unquote(hName)
		originFileName = urllib.parse.unquote(originFileName)
		fName = "%s - %s" % (originFileName, hName)
		fqFName = os.path.join(target_dir, fName)

		# This call also inserts the file parameters into the row
		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup
			fqFName = self.save_archive(row, sess, fqFName, content)

		#self.log.info( filePath)

		with self.row_context(dbid=link_row_id) as row:
			row.state = 'processing'

		# We don't want to upload the file we just downloaded, so specify doUpload as false.
		# As a result of this, the seriesName paramerer also no longer matters
		self.processDownload(seriesName=False, archivePath=fqFName, doUpload=False)


		self.log.info( "Done")
		with self.row_context(dbid=link_row_id) as row:
			row.state = 'complete'
			row.downloaded_at = datetime.datetime.now()
			row.last_checked = datetime.datetime.now()

		return


	def setup(self):
		# Muck about in the webget internal settings
		self.wg.errorOutCount = 4
		self.wg.retryDelay    = 5




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = ContentLoader()
		run.do_fetch_content()


