
# -*- coding: utf-8 -*-

import os
import re
import datetime
import os.path

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error
import traceback

import urllib
import json
import ast
import settings
import bs4
import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase

import MangaCMS.ScrapePlugins.ScrapeExceptions as ScrapeExceptions

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Hentai2Read.Cl"
	plugin_name = "Hentai2Read Content Retreiver"
	plugin_key   = "h2r"
	is_manga     = False
	is_hentai    = True
	is_book      = False

	urlBase    = "https://hentai2read.com/"

	retreivalThreads = 1

	itemLimit = 1000
	# itemLimit = 1

	shouldCanonize = False

	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()


	def build_links(self, pageurl, root_url, item_meta):
		ret = []

		for imgurl in item_meta['images']:
			imgurl = imgurl.replace("\\", "")
			imgurl = urllib.parse.urljoin(root_url, "/hentai" + imgurl)

			ret.append((imgurl, pageurl))

		return ret

	def getDownloadInfo(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			source_url  = row.source_id
			row.state   = 'fetching'

		self.log.info("Retrieving item: %s", source_url)

		try:
			soup = self.wg.getSoup(source_url, addlHeaders={'Referer': self.urlBase})
		except:
			self.log.critical("No download at url %s!", source_url)
			raise IOError("Invalid webpage")


		scripts = soup.find_all("script")

		iteminfo = None
		for script in scripts:
			scriptt = script.get_text(strip=True)
			if 'var gData' in scriptt:
				scriptt = scriptt.replace("var gData = ", "").strip(";")
				iteminfo = ast.literal_eval(scriptt)

		if not iteminfo:
			raise IOError("Failed to extract item information")

		first_img_url = soup.find("img", id='arf-reader')

		imageUrls = self.build_links(source_url, first_img_url["src"], iteminfo)

		self.log.info("Found %s image urls!", len(imageUrls))

		ret = {
				"dl_links"    : imageUrls,
				"source_url"  : source_url,
			}

		return ret

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True)
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def fetchImages(self, image_list):

		images = []
		for imgurl, referrerurl in image_list:
			images.append(self.getImage(imgurl, referrerurl))

		return images



	def doDownload(self, link_info, link_row_id):

		images = self.fetchImages(link_info['dl_links'])

		if not images:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False


		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup
			series_name = row.series_name

			fileN = row.origin_name + ".zip"
			fileN = nt.makeFilenameSafe(fileN)

			fqFName = os.path.join(settings.asmhSettings["dlDir"], nt.makeFilenameSafe(series_name), fileN)

			fqFName = self.save_image_set(row, sess, fqFName, images)

		self.processDownload(seriesName=False, archivePath=fqFName, doUpload=False)

		with self.row_context(dbid=link_row_id) as row:
			row.state = 'complete'

			row.downloaded_at = datetime.datetime.now()
			row.last_checked = datetime.datetime.now()

		return True


	def get_link(self, link_row_id):
		try:
			link_info = self.getDownloadInfo(link_row_id=link_row_id)
			self.doDownload(link_info=link_info, link_row_id=link_row_id)
		except urllib.error.URLError:
			self.log.error("Failure retrieving content for link %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()

		except IOError:
			self.log.error("Failure retrieving content for link %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()

if __name__ == "__main__":
	import utilities.testBase as tb

	# with tb.testSetup():
	with tb.testSetup(load=False):

		run = ContentLoader()

		# run.retreivalThreads = 1
		# run._resetStuckItems()
		run.do_fetch_content()
		# test = {
		# 	'sourceUrl'  : 'https://asmhentai.com/g/178575/',
		# 	'seriesName' : 'Doujins',
		# }
		# run.getDownloadInfo(test)



