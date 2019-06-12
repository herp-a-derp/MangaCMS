
# -*- coding: utf-8 -*-

import os
import re
import os.path
import datetime

import zipfile
import nameTools as nt

import urllib.request, urllib.parse, urllib.error
import traceback

import urllib
import settings
import bs4
import MangaCMS.ScrapePlugins.RetreivalBase

import MangaCMS.ScrapePlugins.ScrapeExceptions as ScrapeExceptions

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.ASMHentai.Cl"
	plugin_name = "ASMHentai Content Retreiver"
	plugin_key  = "asmh"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase    = "https://asmhentai.com/"


	retreival_threads = 1

	itemLimit = 220

	shouldCanonize = False

	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()


	def build_links(self, imtag, selector):

		imgurl = imtag['src']
		imgurl = urllib.parse.urljoin(self.urlBase, imgurl)


		# This is brittle too
		urlprefix, fname = imgurl.rsplit("/", 1)
		fname, fext = os.path.splitext(fname)


		ret = []


		for item in selector.find_all('option'):
			if item.get("value"):
				pageurl = urllib.parse.urljoin(self.urlBase, item.get("value"))
				pagenum = pageurl.strip("/").split("/")[-1]
				imgurl = urlprefix + "/" + str(pagenum) + fext

				ret.append((imgurl, pageurl))

		return ret

	def getDownloadInfo(self, link_row_id, retag=False):

		with self.row_context(dbid=link_row_id) as row:
			source_url = row.source_id
			row.state = 'fetching'

		self.log.info("Retrieving item: %s", source_url)

		try:
			soup = self.wg.getSoup(source_url, addlHeaders={'Referer': self.urlBase})
		except:
			self.log.critical("No download at url %s! SourceUrl = %s", source_url, link_row_id)
			raise IOError("Invalid webpage")


		read_link = soup.find("a", href=re.compile(r"/gallery/\d+?/\d+?/", re.IGNORECASE))

		nav_to = urllib.parse.urljoin(self.urlBase, read_link['href'])
		soup = self.wg.getSoup(nav_to, addlHeaders={'Referer': source_url})
		if soup.find_all("div", class_="g-recaptcha"):
			raise ScrapeExceptions.LimitedException


		selector = soup.find('select', class_='pag_info')
		imgdiv = soup.find('div', id='img')

		imtag                  = imgdiv.find('img')


		imageUrls = self.build_links(imtag, selector)

		self.log.info("Found %s image urls!", len(imageUrls))

		return imageUrls, imtag['alt']

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content



	def fetchImages(self, image_urls):

		images = []
		for imgUrl, referrerUrl in image_urls:
			images.append(self.getImage(imgUrl, referrerUrl))

		return images


	def doDownload(self, image_urls, origin_name, link_row_id):


		images = self.fetchImages(image_urls)


		if not images:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return


		fileN = origin_name+".zip"

		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup

			container_dir = os.path.join(settings.hbSettings["dlDir"], nt.makeFilenameSafe(row.series_name))

			wholePath = os.path.join(container_dir, fileN)
			fqFName = self.save_image_set(row, sess, wholePath, images)

		with self.row_context(dbid=link_row_id) as row:
			row.state = 'processing'

		# We don't want to upload the file we just downloaded, so specify doUpload as false.
		# As a result of this, the seriesName paramerer also no longer matters
		self.processDownload(seriesName=False, archivePath=fqFName, doUpload=False)


		self.log.info( "Done")
		with self.row_context(dbid=link_row_id) as row:
			row.state = 'complete'
			row.downloaded_at = datetime.datetime.now()
			row.last_checked = datetime.datetime.now()



	def get_link(self, link_row_id):

		try:
			image_urls, origin_name= self.getDownloadInfo(link_row_id=link_row_id)
			self.doDownload(image_urls, origin_name, link_row_id)
		except urllib.error.URLError:
			self.log.error("Failure retrieving content for link_row_id %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'

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



