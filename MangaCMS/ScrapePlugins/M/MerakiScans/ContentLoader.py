

import settings
import os
import os.path

import nameTools as nt


import urllib.parse
import html.parser
import zipfile
import runStatus
import traceback
import bs4
import re
import MangaCMS.ScrapePlugins.RetreivalBase


import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Meraki.Cl"
	plugin_name = "MerakiScans Content Retreiver"
	plugin_key  = "meraki"
	is_manga    = True
	is_hentai   = False
	is_book     = False

	retreivalThreads = 1


	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content


	def getImageUrls(self, baseUrl):

		pageCtnt = self.wg.getpage(baseUrl)
		soup = bs4.BeautifulSoup(pageCtnt, "lxml")

		selector = soup.find("select", class_="cbo_wpm_pag")

		if not selector:
			raise ValueError("Unable to find contained images on page '%s'" % baseUrl)

		pageNumbers = []
		for value in selector.find_all("option"):
			pageNumbers.append(int(value.get_text()))

		if not pageNumbers:
			raise ValueError("Unable to find contained images on page '%s'" % baseUrl)

		pageUrls = []
		for pageNo in pageNumbers:
			pageUrls.append("{baseUrl}{num}/".format(baseUrl=baseUrl, num=pageNo))

		# print("PageUrls", pageUrls)
		imageUrls = []

		for pageUrl in pageUrls:


			pageCtnt = self.wg.getpage(pageUrl)

			soup = bs4.BeautifulSoup(pageCtnt, "lxml")

			imageContainer = soup.find("div", class_="prw")
			url = imageContainer.img["src"]
			# print("Urls - ", (url, pageUrl))
			imageUrls.append((url, pageUrl))

		return imageUrls


	def get_link(self, link_row_id):

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

			images = []

			for image_idx, img_dat in enumerate(imageUrls):
				image_url, referrerUrl = img_dat
				imageName, imageContent = self.getImage(image_url, referrerUrl)
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

			chapter_name = chapter_name + " [MerakiScans]"

			self.save_manga_image_set(link_row_id, series_name, chapter_name, images)

		except Exception:
			self.log.critical("Failure on retrieving content at %s", source_url)
			self.log.critical("Traceback = %s", traceback.format_exc())
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()
			raise




if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup():

		run = ContentLoader()
		run.do_fetch_content()



