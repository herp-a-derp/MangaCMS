
# -*- coding: utf-8 -*-
import datetime
import os
import re
import os.path

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4
import MangaCMS.cleaner.processDownload


import MangaCMS.ScrapePlugins.RetreivalBase

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):



	logger_path = "Main.Manga.NHentai.Cl"
	plugin_name = "NHentai Content Retreiver"
	plugin_key  = "nh"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "http://nhentai.net/"

	retreivalThreads = 1

	shouldCanonize = False

	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()


	def imageUrls(self, soup):
		thumbnailDiv = soup.find("div", id="thumbnail-container")

		ret = []

		for link in thumbnailDiv.find_all("a", class_='gallerythumb'):

			referrer = urllib.parse.urljoin(self.urlBase, link['href'])
			if hasattr(link, "data-src"):
				thumbUrl = link.img['data-src']
			else:
				thumbUrl = link.img['src']

			if not "t." in thumbUrl[-6:]:
				raise ValueError("Url is not a thumb? = '%s'" % thumbUrl)
			else:
				imgUrl = thumbUrl[:-6] + thumbUrl[-6:].replace("t.", '.')

			imgUrl   = urllib.parse.urljoin(self.urlBase, imgUrl)
			imgUrl = imgUrl.replace("//t.", "//i.")

			ret.append((imgUrl, referrer))

		return ret

	def getDownloadInfo(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			source_url = row.source_id
			row.state = 'fetching'


		self.log.info("Retrieving item: %s", source_url)



		try:
			soup = self.wg.getSoup(source_url, addlHeaders={'Referer': self.urlBase})
		except:
			self.log.critical("No download at url %s!", source_url)
			raise IOError("Invalid webpage")

		cat_containers = soup.find_all(text=re.compile("Categories:"))
		series_name = "Unknown"
		for container in cat_containers:
			container = container.parent
			if "tag-container" in container.get("class", []):
				_ = [tmp.decompose() for tmp in container.find_all("span", class_="count")]
				series_name = container.span.get_text(strip=True).title()

		imageUrls = self.imageUrls(soup)

		# print("Image URLS: ", imageUrls)
		ret = {
				"dlLinks"     : imageUrls,
				'series_name' : series_name,
			}


		return ret

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def fetchImages(self, image_list):

		images = []
		for imgUrl, referrerUrl in image_list:
			images.append(self.getImage(imgUrl, referrerUrl))

		return images



	def doDownload(self, linkDict, link_row_id):

		images = self.fetchImages(linkDict["dlLinks"])

		if not images:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return

		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup
			row.series_name = linkDict['series_name']

			fileN = row.origin_name + ".zip"
			fileN = nt.makeFilenameSafe(fileN)

			fqFName = os.path.join(settings.nhSettings["dlDir"], nt.makeFilenameSafe(row.series_name), fileN)

			fqFName = self.save_image_set(row, sess, fqFName, images)

		self.processDownload(seriesName=False, archivePath=fqFName, doUpload=False)

		with self.row_context(dbid=link_row_id) as row:
			row.state = 'complete'
			row.downloaded_at = datetime.datetime.now()
			row.last_checked = datetime.datetime.now()


	def get_link(self, link_row_id):
		try:
			linkInfo = self.getDownloadInfo(link_row_id)
			self.doDownload(linkInfo, link_row_id)
		except urllib.error.URLError:
			self.log.error("Failure retrieving content for link %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
		except IOError:
			self.log.error("Failure retrieving content for link %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.retreivalThreads = 1
		# run.resetStuckItems()
		run.do_fetch_content()
