

import MangaCMS.lib.logSetup
import runStatus

import bs4
import nameTools as nt
import os
import os.path
import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase
import settings
import traceback
import urllib.parse

import zipfile

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):



	logger_path = "Main.Manga.Ms.Cl"
	plugin_name = "MangaStream.com Content Retreiver"
	plugin_key  = "ms"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	retreivalThreads = 2
	urlBase    = "https://readms.net/"

	def getImage(self, imageUrl, referrer):
		if imageUrl.startswith("//"):
			imageUrl = "http:" + imageUrl
		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def getImageUrls(self, baseUrl):
		pages = set()

		nextUrl = baseUrl
		chapBase = baseUrl.rstrip('0123456789.')
		chapBase = urllib.parse.urlsplit(chapBase).path

		imnum = 1
		print("ChapBase:", chapBase)

		while 1:
			assert nextUrl.lower().startswith("http"), "Invalid URL: %s" % nextUrl
			soup = self.wg.getSoup(nextUrl)
			imageDiv = soup.find('div', class_='page')

			if not imageDiv.a:
				raise ValueError("Could not find imageDiv?")
			imgurl = imageDiv.img['src']

			if not imgurl.lower().startswith("http"):
				imgurl = ("http:" if 'http:' in nextUrl else "https:") + imgurl
			pages.add((imnum, imgurl, nextUrl))

			nextUrl = imageDiv.a['href']
			nextUrl = urllib.parse.urljoin(baseUrl, nextUrl)


			if not chapBase in urllib.parse.urlsplit(nextUrl).path:
				break
			imnum += 1

		assert len(pages) > 1


		self.log.info("Found %s pages", len(pages))

		return pages



	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			series_name = row.series_name
			chapter_name = row.origin_name
			source_url = row.source_id
			row.state = 'fetching'

		try:
			self.log.info( "Should retreive url - %s", source_url)

			imageUrls = self.getImageUrls(source_url)

			if not imageUrls:
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'error'
					row.err_str = "error-404"
					return

			images = []

			for image_counter, imgUrl, referrerUrl in imageUrls:
				imageContent, imageName = self.wg.getFileAndName(imgUrl, addlHeaders={'Referer': referrerUrl})
				img_postf = urllib.parse.urlsplit(imgUrl).path.split("/")[-1]
				imageName = "{:04d} - {} {}".format(image_counter, imageName, img_postf)
				self.log.info("Found %s byte image named %s", len(imageContent), imageName)
				images.append([imageName, imageContent])

			self.save_manga_image_set(link_row_id, series_name, chapter_name, images)

		except Exception:
			self.log_exception()
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()
				return

if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup():
		cl = ContentLoader()
		cl.do_fetch_content()

