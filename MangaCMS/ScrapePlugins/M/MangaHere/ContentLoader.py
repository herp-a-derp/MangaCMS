

import MangaCMS.lib.logSetup
import runStatus
if __name__ == "__main__":
	runStatus.preloadDicts = False


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

	logger_path = "Main.Manga.Mh.Cl"
	plugin_name = "MangaHere Content Retreiver"
	plugin_key = "mh"
	is_manga    = True
	is_hentai   = False
	is_book     = False



	retreivalThreads = 1
	itemLimit = 500


	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content


	def proceduralGetImages(self, link):
		baseUrl = link

		images = []
		while baseUrl in link:
			page = self.wg.getSoup(link)
			container = page.find('section', class_='read_img')
			imageContainer = container.find_all('img')

			imgurls = [img['src'] for img in imageContainer if '/media/images/loading.gif' not in img['src']]

			assert len(imgurls) == 1, "Wrong number of images: %s (%s)" % (len(imgurls), imgurls)
			imgUrl = imgurls[0]

			if imgUrl.startswith("//"):
				imgUrl = "http:" + imgUrl


			assert '/media/images/loading.gif' not in imgUrl
			imgdat = self.getImage(imgUrl, link)


			assert imgdat
			assert len(imgdat) == 2
			images.append(imgdat)
			link = container.a['href']

			if link.startswith("//"):
				link = "http:" + link

			self.log.info("Found %s images for release %s so far", len(images), baseUrl)

		self.log.info("Found %s images for release %s total", len(images), baseUrl)

		return images

	def setup(self):
		cf_ok = self.wg.stepThroughJsWaf("http://www.mangahere.co/", titleContains='Manga Here - ')
		self.log.info("CF Access return value: %s", cf_ok)
		if not cf_ok:
			raise ValueError("Could not access site due to cloudflare protection.")


	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			series_name = row.series_name
			chapter_name = row.origin_name
			source_url = row.source_id
			row.state = 'fetching'

		series_name = nt.getCanonicalMangaUpdatesName(series_name)



		self.log.info( "Should retreive url - %s", source_url)

		images = self.proceduralGetImages(source_url)

		if not images:
			self.log.critical("Failure on retrieving content at %s", source_url)
			self.log.critical("Page not found - 404")
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = "error-404"
				return

		imgCnt = 1
		for imageName, imageContent in images:

			imageName = "{num:03.0f} - {srcName}".format(num=imgCnt, srcName=imageName)
			imgCnt += 1
			images.append([imageName, imageContent])

			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'new'
					return


		if not images:
			self.log.error("No images! Download failed?")
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = "error-404"
				return


		self.save_manga_image_set(link_row_id, series_name, chapter_name, images, source_name='MangaHere')


	# def getLink(self, link):

	# 	sourceUrl  = link["sourceUrl"]
	# 	seriesName = link['seriesName']

	# 	try:
	# 		self.log.info( "Should retreive url - %s", sourceUrl)
	# 		self.updateDbEntry(sourceUrl, dlState=1)

	# 		seriesName = nt.getCanonicalMangaUpdatesName(seriesName)

	# 		self.log.info("Downloading = '%s', '%s'", seriesName, link["originName"])
	# 		dlPath, newDir = self.locateOrCreateDirectoryForSeries(seriesName)

	# 		if link["flags"] == None:
	# 			link["flags"] = ""

	# 		if newDir:
	# 			self.updateDbEntry(sourceUrl, flags=" ".join([link["flags"], "haddir"]))

	# 		chapterName = nt.makeFilenameSafe(link["originName"])

	# 		fqFName = os.path.join(dlPath, chapterName+" [MangaHere].zip")

	# 		loop = 1
	# 		prefix, ext = os.path.splitext(fqFName)
	# 		while os.path.exists(fqFName):
	# 			fqFName = "%s (%d)%s" % (prefix, loop,  ext)
	# 			loop += 1
	# 		self.log.info("Saving to archive = %s", fqFName)

	# 		images = self.proceduralGetImages(sourceUrl)

	# 		self.log.info("Creating archive with %s images", len(images))

	# 		if not images:
	# 			self.updateDbEntry(sourceUrl, dlState=-1, tags="error-404")
	# 			return

	# 		fqFName = self.save_image_set(fqFName, images)

	# 		dedupState = MangaCMS.cleaner.processDownload.processDownload(seriesName, fqFName, deleteDups=True, includePHash=True, rowId=link['dbId'])
	# 		self.log.info( "Done")

	# 		filePath, fileName = os.path.split(fqFName)
	# 		self.updateDbEntry(sourceUrl, dlState=2, downloadPath=filePath, fileName=fileName, tags=dedupState)
	# 		return

	# 	except Exception:
	# 		self.log.critical("Failure on retrieving content at %s", sourceUrl)
	# 		self.log.critical("Traceback = %s", traceback.format_exc())
	# 		self.updateDbEntry(sourceUrl, dlState=-1)
	# 		raise

if __name__ == '__main__':
	import utilities.testBase as tb

	# with tb.testSetup():
	with tb.testSetup():
		cl = ContentLoader()
		# cl.proceduralGetImages('http://www.mangahere.co/manga/totsugami/v05/c030/')
		# cl.getLink({'seriesName': 'Totsugami', 'originName': 'Totsugami 32 - Vol 05', 'retreivalTime': 1414512000.0, 'dlState': 0, 'sourceUrl': 'http://www.mangahere.co/manga/totsugami/v05/c032/', 'flags':None})

		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.do_fetch_content()


