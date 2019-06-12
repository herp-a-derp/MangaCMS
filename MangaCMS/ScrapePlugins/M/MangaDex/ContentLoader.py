


import sys
import os
import os.path
import ast
import magic
import urllib.parse
import traceback
import re

import nameTools as nt

import MangaCMS.ScrapePlugins.RetreivalBase
import MangaCMS.ScrapePlugins.RunBase
import MangaCMS.ScrapePlugins.ScrapeExceptions

import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.MDx.Cl"
	plugin_name = "MangaDex Content Retreiver"
	plugin_key  = "mdx"
	is_manga    = True
	is_hentai   = False
	is_book     = False



	retreivalThreads = 1
	urlBase    = "https://mangadex.org/"



	def getImageUrls(self, chapUrl):
		soup = self.wg.getSoup(chapUrl)

		if "Due to the group's delay policy, this chapter will be available in" in str(soup):
			raise MangaCMS.ScrapePlugins.ScrapeExceptions.ContentNotAvailableYetError("Bullshit delay garbage")



		meta_tags = soup.find_all("meta")

		name_tag = [
					tmp
				for
					tmp
				in
					meta_tags
				if
						'name' in tmp.attrs
					and
						'data-chapter-id' in tmp.attrs
					and
						tmp.attrs['name'] == 'app'
			]

		if not (name_tag and len(name_tag) == 1):
			self.log.error("Could not find meta tag on manga page: '%s'", chapUrl)
			return []

		series_id = name_tag[0]['data-chapter-id']

		js_vars = self.wg.getJson('https://mangadex.org/api/chapter/%s?' % series_id)

		expect_keys = ['page_array', 'server', 'hash']
		if not all([key in js_vars for key in expect_keys]):
			self.log.error("Missing content variables from manga page: '%s'", chapUrl)
			self.log.error("JS Data: %s", js_vars)
			return []

		image_urls = []



		for idx, img_file in enumerate(js_vars['page_array']):
			img_url = js_vars['server'] + js_vars['hash'] + "/" + img_file
			img_url = urllib.parse.urljoin(self.urlBase, img_url)
			image_urls.append((img_url, chapUrl + "/%s" % (idx + 1, )))

		self.log.info("Found %s images", len(image_urls))

		return image_urls


	def getImages(self, source_url):

		imageUrls = self.getImageUrls(source_url)

		images = []

		image_counter = 1
		for imgUrl, referrerUrl in imageUrls:
			imageContent, imageName = self.wg.getFileAndName(imgUrl, addlHeaders={'Referer': referrerUrl})
			img_postf = urllib.parse.urlsplit(imgUrl).path.split("/")[-1]
			imageName = "{:04d} - {} {}".format(image_counter, imageName, img_postf)
			self.log.info("Found %s byte image named %s", len(imageContent), imageName)
			images.append([imageName, imageContent])
			image_counter += 1

			fType = magic.from_buffer(imageContent, mime=True)

			if not 'image' in fType:
				raise MangaCMS.ScrapePlugins.ScrapeExceptions.ContentNotAvailableYetError(
					"Empty/failed image return - File isn't an image? Detected type: %s" % fType)

		return images


	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			series_name = row.series_name
			chapter_name = row.origin_name
			source_url = row.source_id
			row.state = 'fetching'


		try:
			self.log.info( "Should retreive url - %s", source_url)

			images = self.getImages(source_url)

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
			raise

if __name__ == '__main__':
	import utilities.testBase as tb

	# with tb.testSetup():
	with tb.testSetup():
		cl = ContentLoader()
		# cl.proceduralGetImages('http://www.MangaDex.co/manga/totsugami/v05/c030/')
		# cl.getLink(
		# 		{
		# 		    'originName': 'D-Frag! - Ch. 69 Thank you very much! [MangaDex, Hot Chocolate Scans]',
		# 		    'downloadPath': None,
		# 		    'sourceUrl': 'https://mangadex.org/chapter/19083',
		# 		    'sourceId': None,
		# 		    # 'retreivalTime': time.struct_time(tm_year = 2018, tm_mon = 1, tm_mday = 28, tm_hour = 5, tm_min = 29, tm_sec = 31, tm_wday = 6, tm_yday = 28, tm_isdst = 0),
		# 		    'dbId': 2943680,
		# 		    'flags': None,
		# 		    'tags': None,
		# 		    'lastUpdate': 0.0,
		# 		    'note': None,
		# 		    'seriesName': 'D-Frag!',
		# 		    'dlState': 0,
		# 		    'fileName': None
		# 		}
		# 	)
		# cl.getLink(
		# 		{
		# 		    'originName': "Mousou Telepathy - Ch. 166 That's Where He's Different [MangaDex, Helvetica Scans]",
		# 		    'downloadPath': None,
		# 		    'sourceUrl': 'https://mangadex.org/chapter/19131',
		# 		    'sourceId': None,
		# 		    # 'retreivalTime': time.struct_time(tm_year = 2018, tm_mon = 1, tm_mday = 28, tm_hour = 5, tm_min = 48, tm_sec = 7, tm_wday = 6, tm_yday = 28, tm_isdst = 0),
		# 		    'dbId': 2943321,
		# 		    'flags': None,
		# 		    'tags': None,
		# 		    'lastUpdate': 0.0,
		# 		    'note': None,
		# 		    'seriesName': 'Mousou Telepathy',
		# 		    'dlState': 0,
		# 		    'fileName': None
		# 		}
		# 	)
		# cl.getLink(
		# 		{
		# 		    'sourceUrl': 'https://mangadex.org/chapter/19151',
		# 		    'lastUpdate': 0.0,
		# 		    'dbId': 2943493,
		# 		    # 'retreivalTime': time.struct_time(tm_year = 2018, tm_mon = 1, tm_mday = 28, tm_hour = 6, tm_min = 25, tm_sec = 24, tm_wday = 6, tm_yday = 28, tm_isdst = 0),
		# 		    'note': None,
		# 		    'sourceId': None,
		# 		    'flags': None,
		# 		    'seriesName': 'Yakumo-san wa Edzuke ga Shitai.',
		# 		    'fileName': None,
		# 		    'dlState': 0,
		# 		    'tags': None,
		# 		    'originName': "Yakumo-san wa Edzuke ga Shitai. - Vol. 5 Ch. 29 Yamato's Answer [MangaDex, /a/nonymous]",
		# 		    'downloadPath': None
		# 		}
		# 	)

		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.do_fetch_content()


