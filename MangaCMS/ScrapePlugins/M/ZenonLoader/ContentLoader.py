

import MangaCMS.lib.logSetup
import runStatus
if __name__ == "__main__":
	runStatus.preloadDicts = False



import settings
import os
import os.path

import nameTools as nt

import time
import datetime

import urllib.parse
import html.parser
import zipfile
import traceback
import bs4
import re
import json
import MangaCMS.ScrapePlugins.RetreivalBase
from mimetypes import guess_extension
from concurrent.futures import ThreadPoolExecutor

import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Ze.Cl"
	plugin_name = "Comic-Zenon Magazine Content Retreiver"
	plugin_key = "ze"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)

		if not "." in fileN:
			info = handle.info()
			if 'Content-Type' in info:
				tp = info['Content-Type']
				if ";" in tp:
					tp = tp.split(";")[0]
				ext = guess_extension(tp)
				if ext == None:
					ext = "unknown_ftype"
				print(info['Content-Type'], ext)
				fileN += "." + ext
			else:
				fileN += ".jpg"


		return fileN, content



	def getImageUrlsInfo(self, baseUrl):

		soup = self.wg.getSoup(baseUrl)

		container = soup.find("div", class_='swiper-wrapper')
		# print(container)

		imgs = container.find_all("img")


		pages = []
		for item in imgs:
			pages.append(item['data-src'])

		self.log.info("Found %s pages", len(pages))

		meta = {}

		minfo = soup.find("meta", property="og:title")
		meta['series_name'] = minfo['content'].split("#", 1)[0].strip()
		meta['rel_name']    = minfo['content'].split("|", 1)[0].strip()
		return pages, meta




	def get_link(self, link_row_id):


		with self.row_context(dbid=link_row_id) as row:
			source_url = row.source_id
			row.state = 'fetching'



		try:
			self.log.info( "Should retreive url - %s", source_url)
			# self.updateDbEntry(source_url, dlState=1)

			imageUrls, meta = self.getImageUrlsInfo(source_url)

			if not imageUrls:
				self.log.critical("Failure on retrieving content at %s", source_url)
				self.log.critical("Page not found - 404")
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return



			if not imageUrls:
				self.log.critical("Failure on retrieving content at %s", source_url)
				self.log.critical("Page not found - 404")
				# self.updateDbEntry(source_url, dlState=-1)
				return

			self.log.info("Downloading = '%s', '%s' ('%s images)", meta['series_name'], meta['rel_name'], len(imageUrls))

			images = []
			imgCnt = 1
			for imgUrl in imageUrls:
				imageName, imageContent = self.getImage(imgUrl, source_url)
				imageName = "{num:03.0f} - {srcName}".format(num=imgCnt, srcName=imageName)
				imgCnt += 1
				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					# self.updateDbEntry(source_url, dlState=0)
					return

			self.log.info("Creating archive with %s images", len(images))

			if not images:
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return

			with self.row_context(dbid=link_row_id) as row:
				row.series_name = meta['series_name']
				row.origin_name = meta['rel_name']


			chapter_name = nt.makeFilenameSafe(meta['rel_name']) + " [ComicZenon]"

			self.save_manga_image_set(link_row_id, meta['series_name'], chapter_name, images)



		except Exception:
			self.log.critical("Failure on retrieving content at %s", link_row_id)
			self.log.critical("Traceback = %s", traceback.format_exc())
			# self.updateDbEntry(sourceUrl, dlState=-1)
			raise



if __name__ == '__main__':
	import pprint
	import utilities.testBase as tb

	# with tb.testSetup(startObservers=True):
	with tb.testSetup(load=False):
		cl = ContentLoader()

		# pg = 'http://dynasty-scans.com/chapters/qualia_the_purple_ch16'
		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		# cl.do_fetch_content()


		urls = [
				'http://comic.manga-audition.com/entries/angel-heart-by-tsukasa-hojo-chapter001/',
				'http://smacmag.net/v/arte/arte-by-kei-ohkubo-chapter017/',
				'http://comic.manga-audition.com/entries/nobo-and-her-by-molico-ross-chapter001/',
			]
		# link = {
		# 		'downloadPath'  : None,
		# 		'retreivalTime' : datetime.datetime.now(),
		# 		'lastUpdate'    : 0.0,
		# 		'sourceId'      : None,
		# 		'originName'    : None,
		# 		'tags'          : None,
		# 		'dbId'          : 840370,
		# 		'dlState'       : 0,
		# 		'note'          : None,
		# 		'sourceUrl'     : None,  # Insert here
		# 		'seriesName'    : None,
		# 		'fileName'      : None,
		# 		'flags'         : None
		# 	}

		# for url in urls:
		# 	link['sourceUrl'] = url
		# 	cl.getLink(link)

		for url in urls:
			vals = cl.getImageUrlsInfo(url)
			pprint.pprint(vals)


