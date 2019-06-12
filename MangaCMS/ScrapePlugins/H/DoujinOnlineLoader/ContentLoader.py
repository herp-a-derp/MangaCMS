
# -*- coding: utf-8 -*-

import re

import os
import os.path
import sys

import random
import datetime
import json
import sys
import zipfile

import datetime
import pprint
import urllib.parse
import traceback

import bs4


import runStatus
runStatus.preloadDicts = False
import nameTools as nt
import settings

import WebRequest
import MangaCMS.cleaner.processDownload

import MangaCMS.ScrapePlugins.RetreivalBase

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):

	logger_path = "Main.Manga.DoujinOnline.Cl"
	plugin_name = "DoujinOnline Content Retreiver"
	plugin_key  = "dol"
	is_manga    = False
	is_hentai   = True
	is_book     = False


	urlBase = "https://doujinshi.online/"

	retreivalThreads = 1

	itemLimit = 220


	def getFileName(self, soup):
		title = soup.find("h1")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text().strip()


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


	def format_tag(self, tag_raw):

		tag = tag_raw.strip()
		while "  " in tag:
			tag = tag.replace("  ", " ")
		tag = tag.strip().replace(" ", "-")
		return tag.lower()

	def getCategoryTags(self, soup):
		tagdiv = soup.find("div", class_='tagbox')
		tagps = tagdiv.find_all("p")

		tags = []

		category = "Unknown?"
		artist_str = "unknown artist"

		formatters = {
						"tags"       : "",
						"artist"     : "artist",
						"group"      : "group",
						"characters" : "character",
						"language"   : "language",
						"series"     : "series",
						"type"       : "type",
					}


		for item in tagps:
			what = item.get_text(strip=True).split(":")[0].lower().strip()
			if not what in formatters:
				self.log.error("Unknown metadata key: %s", what)
				continue

			tags_strings = item.find_all("a", rel='tag')
			tags_strings = [tmp.get_text(strip=True) for tmp in tags_strings]
			tags_strings = [tmp for tmp in tags_strings if tmp != "N/A"]

			if tags_strings and what == 'artist':
				artist_str = tags_strings[0]

			for tag_str in tags_strings:
				tag = " ".join([formatters[what], tag_str])
				tag = self.format_tag(tag)
				tags.append(tag)

		cat = soup.find("a", rel="category")

		if cat:
			category = cat.get_text(strip=True)

		return category, tags, artist_str

	def getDownloadInfo(self, soup):
		ret = {}

		infoSection = soup.find("div", id='infobox')
		category, tags, artist = self.getCategoryTags(infoSection)

		ret['category'] = category
		ret['tags']     = tags
		ret['artist']   = artist
		ret['title']    = self.getFileName(infoSection)
		ret['tags']     = tags

		return ret

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def getImages(self, referrer, soup):

		postdiv = soup.find('div', id="post")
		if not postdiv.script:
			self.log.error("No script tag on page!")
			return []
		scripttxt = postdiv.script.get_text()
		scriptre = re.compile(r'var js_array = (\[.*?),\];//', flags=re.IGNORECASE)
		match = scriptre.search(scripttxt)
		if not match:
			self.log.error("No image array on page!")
			return []

		# Translate annoying javascript literal to something json compatible.
		data_array = match.group(1) + "]"
		imageurls = json.loads(data_array)


		if not imageurls:
			return []

		images = []
		count = 1
		for imageurl in imageurls:
			dummy_garbage_name, imgf = self.getImage(imageurl, referrer)
			intn = "%04d.jpeg" % (count, )
			images.append((intn, imgf))
			count += 1

		return images


	def get_link(self, link_row_id):

		images = None

		with self.row_context(dbid=link_row_id) as row:
			source_url = row.source_id
			row.state = 'fetching'

		try:

			self.log.info("Retrieving item: %s", source_url)
			soup = self.wg.getSoup(source_url, addlHeaders={'Referer': 'https://doujinshi.online/'})
			if not soup:
				self.log.critical("No download at url %s!", source_url)
				raise IOError("Invalid webpage")

			dl_info = self.getDownloadInfo(soup)


			with self.row_context(dbid=link_row_id) as row:
				assert dl_info['tags']
				self.update_tags(dl_info['tags'], row=row)

				row.series_name = dl_info['category']
				row.origin_name = dl_info['title']
				row.lastUpdate  = datetime.datetime.now()

			images = self.getImages(referrer=source_url, soup=soup)


		except WebRequest.WebGetException:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False

		if not (images and dl_info['title']):
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False


		fileN = dl_info['title']+" - "+dl_info['artist']+".zip"
		fileN = nt.makeFilenameSafe(fileN)

		container_dir = os.path.join(settings.djOnSettings["dlDir"], nt.makeFilenameSafe(dl_info['category']))

		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup

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

		return True


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.getLink({'sourceUrl':'https://doujinshi.online/graffiti/'})
		# run.getLink({'sourceUrl':'https://doujinshi.online/hishoku-yuusha-plus/'})
		# run.getDownloadInfo({'sourceUrl':'https://doujinshi.online/cherry-pink-na-kougai-souguu/'})
		run.do_fetch_content()

