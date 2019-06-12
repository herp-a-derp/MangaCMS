

import MangaCMS.lib.logSetup
import runStatus
if __name__ == "__main__":
	runStatus.preloadDicts = False


import WebRequest
import datetime
import settings
import os
import os.path


import time
import sys

import urllib.parse
import html.parser
import zipfile
import traceback
import bs4
import re
import json
from mimetypes import guess_extension
from concurrent.futures import ThreadPoolExecutor

import magic
import threading
import nameTools as nt

import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase
import MangaCMS.ScrapePlugins.ScrapeExceptions as ScrapeExceptions


class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.Ki.Cl"
	plugin_name = "Kiss Manga Content Retreiver"
	plugin_key  = "ki"
	is_manga    = True
	is_hentai   = False
	is_book     = False



	retreivalThreads = 1

	itemLimit = 500

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.cr_lock = threading.Lock()

	def check_recaptcha(self, pgurl, soup=None, markup=None):
		if markup:
			soup = WebRequest.as_soup(markup)
		if not soup:
			raise RuntimeError("You have to pass either the raw page markup, or a pre-parsed bs4 soup object!")

		capdiv = soup.find("div", class_='g-recaptcha')
		if not capdiv:
			if markup:
				return markup
			return soup

		raise ScrapeExceptions.LimitedException("Encountered ReCaptcha! Cannot circumvent!")

		self.log.warning("Found ReCaptcha div. Need to circumvent.")
		sitekey = capdiv['data-sitekey']

		# soup.find("")


		params = {
			'key'       : settings.captcha_solvers['2captcha']['api_key'],
			'method'    : 'userrecaptcha',
			'googlekey' : sitekey,
			'pageurl'   : pgurl,
			'json'      : 1,
		}

		# self.wg.getJson("https://2captcha.com/in.php", postData=params)

		# # here we post site key to 2captcha to get captcha ID (and we parse it here too)
		# captcha_id = s.post("?key={}&method=userrecaptcha&googlekey={}&pageurl={}".format(API_KEY, site_key, url), proxies=proxy).text.split('|')[1]

		# # then we parse gresponse from 2captcha response
		# recaptcha_answer = s.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(API_KEY, captcha_id), proxies=proxy).text
		# print("solving ref captcha...")
		# while 'CAPCHA_NOT_READY' in recaptcha_answer:
		# 	sleep(5)
		# 	recaptcha_answer = s.get("http://2captcha.com/res.php?key={}&action=get&id={}".format(API_KEY, captcha_id), proxies=proxy).text
		# recaptcha_answer = recaptcha_answer.split('|')[1]

		# # we make the payload for the post data here, use something like mitmproxy or fiddler to see what is needed
		# payload = {
		# 	'key': 'value',
		# 	'gresponse': recaptcha_answer  # This is the response from 2captcha, which is needed for the post request to go through.
		# 	}

		resolved = {
			"reUrl"                : "/Manga/Love-Lab-MIYAHARA-Ruri/Vol-010-Ch-001?id=359632",
			"g-recaptcha-response" : "03AOP2lf5kLccgf5aAkMmzXR8mN6Kv6s76BoqHIv-raSzGCa98HMPMdx0n04ourhM1mBApnesMRbzr2vFa0264mY83SCkL5slCFcC-i3uWJoHIjVhGh0GN4yyswg5-yZpDg1iK882nPuxEeaxb18pOK790x4Z18ib5UOPGU-NoECVb6LS03S3b4fCjWwRDLNF43WhkHDFd7k-Os7ULCgOZe_7kcF9xbKkovCh2uuK0ytD7rhiKnZUUvl1TimGsSaFkSSrQ1C4cxZchVXrz7kIx0r6Qp2hPr2_PW0CAutCkmr9lt9TS5n0ecdVFhdVQBniSB-NZv9QEpbQ8",
		}
		# # then send the post request to the url
		# response = s.post(url, payload, proxies=proxy)


	def getImage(self, imageUrl):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True)
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % imageUrl)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)

		if not "." in fileN:
			info = handle.info()
			if 'Content-Type' in info:
				tp = info['Content-Type']
				if ";" in tp:
					tp = tp.split(";")[0]
				ext = guess_extension(tp)
				if ext == None:
					ext = "unknown_ftype"
				print(info['Content-Type'], ext)
				fileN += "." + ext
			else:
				fileN += ".jpg"

		# Let magic figure out the files for us (it's probably smarter then kissmanga, anyways.)
		guessed = magic.from_buffer(content, mime=True)
		ext = guess_extension(guessed)
		if ext:
			fileN = fileN + ext

		return fileN, content


	def getImages(self, baseUrl):

		with self.wg.chromiumContext() as cr:

			resp = cr.blocking_navigate_and_get_source(baseUrl)
			pgctnt = self.check_recaptcha(pgurl=baseUrl, markup=resp['content'])
			linkRe = re.compile(r'lstImages\.push\((wrapKA\(".+?"\))\);')
			links = linkRe.findall(pgctnt)

			pages = []
			for item in links:
				resp_asm = cr.execute_javascript("function() { return %s; }" % item, returnByValue=True)

				# This is horrible.
				tgt = resp_asm['result']['result']['value']['value']

				if not tgt.startswith("http"):
					raise ScrapeExceptions.LimitedException("URL Decryption failed!")
				pages.append(tgt)

			self.log.info("Found %s pages", len(pages))

			self.wg._syncOutOfChromium(cr)

			images = []
			for imgUrl in pages:
				imageName, imageContent = self.getImage(imgUrl)
				images.append((imageName, imageContent))
		return images

	# Don't download items for 12 hours after relase,
	# so that other, (better) sources can potentially host
	# the items first.
	def checkDelay(self, inTime):
		return inTime < (datetime.datetime.now() - datetime.timedelta(seconds=60*60*12))



	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			series_name = row.series_name
			chapter_name = row.origin_name
			source_url = row.source_id
			row.state = 'fetching'



		self.log.info( "Should retreive url - %s", source_url)

		images = self.getImages(source_url)
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
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = "error-404"
				return


		self.save_manga_image_set(link_row_id, series_name, chapter_name, images, source_name='KissManga')



	def setup(self):
		'''
		poke through cloudflare
		'''
		if not self.wg.stepThroughJsWaf("http://kissmanga.com", 'KissManga'):
			raise ValueError("Could not access site due to cloudflare protection.")


if __name__ == '__main__':
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		cl = ContentLoader()

		# pg = 'http://dynasty-scans.com/chapters/qualia_the_purple_ch16'
		# inMarkup = cl.wg.getpage(pg)
		# cl.getImageUrls(inMarkup, pg)
		cl.do_fetch_content()
		# cl.getLink('http://www.webtoons.com/viewer?titleNo=281&episodeNo=3')
		# cl.getImageUrls('http://kissmanga.com/Manga/Hanza-Sky/Ch-031-Read-Online?id=225102')


