
# -*- coding: utf-8 -*-

import re
import os
import os.path
import datetime

import mimetypes
import zipfile

import WebRequest
import urllib.request, urllib.parse, urllib.error

import nameTools as nt

import traceback

import settings
import bs4
import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase

import MangaCMS.ScrapePlugins.ScrapeExceptions as ScrapeExceptions

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Tsumino.Cl"
	plugin_name = "Tsumino Content Retreiver"
	plugin_key  = "ts"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "http://www.tsumino.com/"

	retreivalThreads = 1

	itemLimit = 220

	shouldCanonize = False

	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()


	def imageUrls(self, ref_url, jdat):
		ret = []

		for img_hash in jdat['reader_page_urls']:

			imgurl = "http://www.tsumino.com/Image/Object?name={}".format(urllib.parse.quote(img_hash, safe=''))

			ret.append((imgurl, ref_url))

		return ret


	def handle_recaptcha(self, soup, containing_page, referrer_url):
		self.log.warning("Hit recaptcha. Attempting to solve.")

		key = settings.captcha_solvers['anti-captcha']['api_key']
		solver = WebRequest.AntiCaptchaSolver(api_key=key, wg=self.wg)

		args = {
				tag['id'] : tag['value']
			for
				tag
			in
				soup.find_all('input', id=True)
		}

		captcha_key = soup.find("div", class_="g-recaptcha")['data-sitekey']

		self.log.info("Captcha key: %s with input values: %s", captcha_key, args)

		recaptcha_response = solver.solve_recaptcha(google_key=captcha_key, page_url=containing_page)

		self.log.info("Captcha solved with response: %s", recaptcha_response)
		args['g-recaptcha-response'] = recaptcha_response

		solved_soup = self.wg.getSoup(
				urllib.parse.urljoin(self.urlBase, "/Read/AuthProcess"),
				postData    = args,
				addlHeaders = {'Referer': 'http://www.tsumino.com/Read/Auth/{id}'.format(id=args['Id'])},
			)

		return solved_soup


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



		read_link = soup.find("a", class_='book-read-button', href=re.compile("/read/view", re.IGNORECASE))

		nav_to = urllib.parse.urljoin(self.urlBase, read_link['href'])
		soup = self.wg.getSoup(nav_to, addlHeaders={'Referer': source_url})
		if soup.find_all("div", class_="g-recaptcha"):
			soup = self.handle_recaptcha(soup, nav_to, source_url)

		if soup.find_all("div", class_="g-recaptcha"):
			self.log.error("Failed after attempting to solve recaptcha!")
			raise ScrapeExceptions.LimitedException

		# This is probably brittle
		mid = read_link['href'].split("/")[-1]

		page_params = {
			"q"         : mid,
		}
		addlHeaders = {
			"X-Requested-With" : "XMLHttpRequest",
			"Referer"          : nav_to,
			"Host"             : "www.tsumino.com",
			"Origin"           : "http://www.tsumino.com",
			"Content-Type"     : "application/x-www-form-urlencoded; charset=UTF-8",
			"Cache-Control"    : "no-cache",
			"Pragma"           : "no-cache",
		}

		try:
			jdat = self.wg.getJson("http://www.tsumino.com/Read/Load", postData=page_params, addlHeaders=addlHeaders)
		except Exception as e:
			for line in traceback.format_exc().split("\n"):
				self.log.error(line)

			raise RuntimeError


		return self.imageUrls(source_url, jdat)

	def getImage(self, imageUrl, referrer, fidx):

		content, fname, mimetype = self.wg.getFileNameMime(imageUrl, addlHeaders={'Referer': referrer})
		if not content:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fext = mimetypes.guess_extension(mimetype)

		# Assume jpeg if we can't figure it out, because it's probably safe.
		if fext == '.a' or fext == '.jpe' or not fext:
			fext = ".jpg"

		filename = "{orig} {counter}{ext}".format(
				orig    = fname,
				counter = str(fidx).zfill(4),
				ext     = fext,
			)

		self.log.info("retreived image '%s' with a size of %0.3f K", filename, len(content)/1000.0)
		return filename, content


	def fetchImages(self, image_urls):

		images = []
		fidx = 1
		for imgUrl, referrerUrl in image_urls:
			images.append(self.getImage(imgUrl, referrerUrl, fidx))
			fidx += 1

		return images


	def doDownload(self, image_urls, link_row_id):

		images = self.fetchImages(image_urls)


		if not images:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return

		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup
			if row.series_name:
				fileN = row.series_name + " - " + row.origin_name + ".zip"
			else:
				fileN = "(Unknown)" + " - " + row.origin_name + ".zip"

			container_dir = os.path.join(settings.tsSettings["dlDir"], nt.makeFilenameSafe(row.series_name))

			wholePath = os.path.join(container_dir, fileN)

			try:
				fqFName = self.save_image_set(row, sess, wholePath, images)
			except AssertionError:
				with self.row_context(dbid=link_row_id) as row:
					row.state = 'new'
					return

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

		return True

	def get_link(self, link_row_id):

		try:
			image_urls= self.getDownloadInfo(link_row_id=link_row_id)
			self.doDownload(image_urls=image_urls, link_row_id=link_row_id)
		except urllib.error.URLError:
			self.log.error("Failure retrieving content for link_row_id %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'



	def setup(self):
		self.wg.stepThroughJsWaf(self.urlBase, titleContains="Tsumino")

if __name__ == "__main__":
	import utilities.testBase as tb

	# with tb.testSetup():
	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.retreivalThreads = 1
		# run.getDownloadInfo({
		# 	'sourceUrl'  : 'http://www.tsumino.com/Book/Info/35748/souzouryoku-seiyoku-',
		# 	'seriesName' : 'Test',
		# 	})
		run.do_fetch_content()
		# run.getDownloadInfo("http://www.tsumino.com/Book/Info/27758/1/the-you-behind-the-lens-fakku")
