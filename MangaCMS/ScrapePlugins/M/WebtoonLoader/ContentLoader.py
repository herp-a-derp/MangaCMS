

import MangaCMS.lib.logSetup
import runStatus

import settings
import os
import os.path

import nameTools as nt

import time

import urllib.parse
import html.parser
import zipfile
import traceback
import bs4
import re
import json
import MangaCMS.ScrapePlugins.RetreivalBase

from concurrent.futures import ThreadPoolExecutor

import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):



	logger_path = "Main.Manga.Wt.Cl"
	plugin_name = "Webtoons.com Scans Content Retreiver"
	plugin_key = "wt"
	is_manga    = True
	is_hentai   = False
	is_book     = False

	retreivalThreads = 1

	urlBase = "http://www.webtoons.com/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def getImageUrls(self, baseUrl):



		pages = []

		pageCtnt = self.wg.getpage(baseUrl)
		soup = bs4.BeautifulSoup(pageCtnt, "lxml")

		imagesContainer = soup.find('div', class_='viewer_img')
		images = imagesContainer.find_all("img")
		for image in images:
			if hasattr(image, 'data-url'):
				pages.append((image['data-url'], baseUrl))
				# pages[image['data-url']] = baseUrl
			else:
				raise ValueError("Missing 'data-url'? Page = '%s'", baseUrl)



		self.log.info("Found %s pages", len(pages))

		return pages




	# def getLink(self, link):
	def get_link(self, link_row_id):

		# sourceUrl  = link["sourceUrl"]
		# series_name = link["series_name"]
		# chapter_name = link["originName"]

		with self.row_context(dbid=link_row_id) as row:
			chapter_name = row.origin_name
			source_url = row.source_id
			row.state = 'fetching'
			series_name = row.series_name


		try:
			self.log.info( "Should retreive url - %s", source_url)

			imageUrls = self.getImageUrls(source_url)
			if not imageUrls:
				self.log.critical("Failure on retrieving content at %s", source_url)
				self.log.critical("Page not found - 404")
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return




			self.log.info("Downloading = '%s', '%s' ('%s images)", series_name, chapter_name, len(imageUrls))


			chapter_name = nt.makeFilenameSafe(chapter_name)

			chapter_name = chapter_name + " [webtoons.com].zip"

			images = []

			imgCnt = 1
			for imgUrl, referrerUrl in imageUrls:
				imageName, imageContent = self.getImage(imgUrl, referrerUrl)
				imageName = "{num:03.0f} - {srcName}".format(num=imgCnt, srcName=imageName)
				imgCnt += 1
				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					with self.row_context(dbid=link_row_id) as row:
						row.state = 'new'
						return

			self.log.info("Creating archive with %s images", len(images))

			if not images:
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return


			self.save_manga_image_set(link_row_id, series_name, chapter_name, images)


		except Exception:
			self.log.critical("Failure on retrieving content at %s", source_url)
			self.log.critical("Traceback = %s", traceback.format_exc())
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()

if __name__ == '__main__':

	import utilities.testBase as tb

	with tb.testSetup(load=False):

		cl = ContentLoader()
		print("CL", cl)
		cl.do_fetch_content()
	# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')



	print("Plugin has exited?")

