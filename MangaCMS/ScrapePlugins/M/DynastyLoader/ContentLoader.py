

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
import sqlalchemy.exc
import MangaCMS.ScrapePlugins.RetreivalBase

from concurrent.futures import ThreadPoolExecutor

import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Dy.Cl"
	plugin_name = "Dynasty Scans Content Retreiver"
	plugin_key  = "dy"
	is_manga    = True
	is_hentai   = False
	is_book     = False



	retreivalThreads = 2

	urlBase = "https://dynasty-scans.com/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def getImageUrls(self, inMarkup, baseUrl):

		pages = {}


		jsonRe = re.compile(r'var pages = (\[.*?\]);')

		pg = jsonRe.findall(inMarkup)
		if len(pg) != 1:
			self.log.error("Erroring page '%s'", baseUrl)
			raise ValueError("Page has more then one json section?")

		images = json.loads(pg.pop())

		for index, item in enumerate(images):
			imgurl = urllib.parse.urljoin(baseUrl, item['image'])
			pages[imgurl] = (index, baseUrl)

		self.log.info("Found %s pages", len(pages))

		return pages


	def getSeries(self, markup):
		soup = bs4.BeautifulSoup(markup, "lxml")
		title = soup.find("h3", id='chapter-title')

		if title.b.find('a'):
			title = title.b.a.get_text()

		else:
			title = title.b.get_text()

		title = nt.getCanonicalMangaUpdatesName(title)
		print("Title '%s'" % title)
		return title



	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			chapter_name = row.origin_name
			source_url = row.source_id
			row.state = 'fetching'

		if source_url.startswith("http://"):
			with self.row_sess_context(dbid=link_row_id) as (row, sess):
				try:
					source_url = source_url.replace("http://", "https://")
					row.source_id = source_url
					sess.commit()

				except (sqlalchemy.exc.InvalidRequestError, sqlalchemy.exc.IntegrityError):
					sess.rollback()
					self.log.error("Already fetched HTTPS version (%s). ", source_url)
					sess.delete(row)
					sess.commit()
					self.log.error("Row deleted. ")
					return


		try:
			inMarkup = self.wg.getpage(source_url)

			series_name = self.getSeries(inMarkup)



			self.log.info( "Should retreive url - %s", source_url)

			imageUrls = self.getImageUrls(inMarkup, source_url)
			if not imageUrls:
				self.log.critical("Failure on retrieving content at %s", source_url)
				self.log.critical("Page not found - 404")
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return


			images = []
			image_keys = list(imageUrls.keys())
			image_keys.sort()

			# for imgUrl, referrerUrl in imageUrls.items():
			for imgUrl in image_keys:
				image_idx, referrerUrl = imageUrls[imgUrl]
				imageName, imageContent = self.getImage(imgUrl, referrerUrl)
				imageName = "{:04d} - {}".format(image_idx, imageName)
				images.append([imageName, imageContent])

				if not runStatus.run:
					self.log.info( "Breaking due to exit flag being set")
					with self.row_context(dbid=link_row_id) as row:
						row.state = 'new'
						return

			if not images:
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return

			chapter_name = chapter_name + " [DynastyScans]"

			self.save_manga_image_set(link_row_id, series_name, chapter_name, images)



		except Exception:
			self.log.critical("Failure on retrieving content at %s", source_url)
			self.log.critical("Traceback = %s", traceback.format_exc())
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()
			raise




if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		cl = ContentLoader()

		# pg = 'http://dynasty-scans.com/chapters/qualia_the_purple_ch16'
		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.do_fetch_content()
		# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')


