
import urllib.parse
import traceback
import bs4


import runStatus
import MangaCMS.ScrapePlugins.RetreivalBase
import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Kw.Cl"
	plugin_name = "Kawaii-Scans Content Retreiver"
	plugin_key  = "kw"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	retreivalThreads = 1

	urlBase = "http://kawaii.ca/reader/"

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content


	def getImagePages(self, chapBaseUrl):
		soup = self.wg.getSoup(chapBaseUrl)
		ret = []

		pager = soup.find("div", class_="pager")
		spans = pager.find_all('span')
		if len(spans) != 3:
			self.log.error("Invalid span items! Page: '%s'", chapBaseUrl)
			return ret

		dummy_series, dummy_chapter, pages = spans

		for page in pages.find_all('option'):

			pageUrl = '{chapUrl}/{pageno}'.format(chapUrl=chapBaseUrl, pageno=page['value'])
			ret.append(pageUrl)


		return ret

	def getImageUrls(self, chapUrl):

		pages = {}

		pageBases = self.getImagePages(chapUrl)

		for idx, pageBase in enumerate(pageBases):
			soup = self.wg.getSoup(pageBase)

			image = soup.find("img", class_='picture')

			# I'm.... actually not sure how the url they're using
			# works in-browser, since it doesn't appear to resolve out properly
			# when inspected in the browser debugger, but works outside of it.
			# Anyways, just hack it together
			imUrl = urllib.parse.urljoin(self.urlBase, urllib.parse.quote(image['src']))
			pages[(idx, imUrl)] = pageBase

		self.log.info("Found %s pages", len(pages))

		return pages


	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			chapter_name = row.origin_name
			source_url = row.source_id
			series_name = row.series_name
			row.state = 'fetching'

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

			image_keys = list(imageUrls.keys())
			image_keys.sort()

			for imgkey in image_keys:
				image_idx, imgUrl = imgkey
				referrerUrl = imageUrls[imgkey]
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

			self.log.info("Creating archive with %s images", len(images))

			chapter_name = chapter_name + " [Kawaii-Scans]"

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
		cl.do_fetch_content()
		# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')


