
# -*- coding: utf-8 -*-

import re

import os
import os.path

import random
import json
import sys
import zipfile

import datetime
import pprint
import urllib.parse
import traceback

import bs4

import nameTools as nt

import settings

import WebRequest

import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):




	logger_path = "Main.Manga.Pururin.Cl"
	plugin_name = "Pururin Content Retreiver"
	plugin_key  = "pu"
	is_manga    = False
	is_hentai   = True
	is_book     = False


	urlBase = "http://pururin.io/"



	retreivalThreads = 2


	def getFileName(self, soup):
		container = soup.find("div", class_='gallery-wrapper')
		# Descriptive, eh?
		link_w_title = container.find("div", class_='title')
		title = link_w_title.get_text(strip=True)

		bad_prefix = "Read "
		bad_postfix = " Online"
		if title.startswith(bad_prefix):
			title = title[len(bad_prefix):]
		if title.endswith(bad_postfix):
			title = title[: -1 * len(bad_postfix)]

		if "/" in title:
			title = title.split("/")[0]

		return title



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


	def getCategoryTags(self, soup):
		container = soup.find("div", class_='gallery-wrapper')
		# Descriptive, eh?
		tagTable = container.find("table", class_="table-gallery-info")

		tags = []

		formatters = {
						"Artist"     : "Artist",
						"Circle"     : "Circles",
						"Parody"     : "Parody",
						"Characters" : "Characters",
						"Contents"   : "",
						"Language"   : "",
						"Scanlator"  : "scanlators",
						"Convention" : "Convention"
					}

		ignoreTags = [
					"Uploader",
					"Pages",
					"Ranking",
					"Rating"]

		category = "Unknown?"
		for tr in tagTable.find_all("tr"):
			if len(tr.find_all("td")) != 2:
				continue

			what, values = tr.find_all("td")

			what = what.get_text()
			if what in ignoreTags:
				continue
			elif what == "Category":
				category = values.get_text().strip()
				if category == "Manga One-shot":
					category = "=0= One-Shot"
			elif what in formatters:
				for li in values.find_all("li"):
					tag_raw = li.get_text(strip=True)
					tag_chunks = [tmp.strip() for tmp in re.split(r"[,\|]", tag_raw) if tmp.strip()]
					for chunk in tag_chunks:
						tag = " ".join([formatters[what], chunk])
						tag = tag.strip()
						tag = tag.replace("  ", " ")
						tag = tag.replace(" ", "-")
						tags.append(tag)

		return category, tags

	def getNote(self, soup):
		note = soup.find("div", class_="gallery-description")
		if note == None:
			note = ""
		else:
			note = note.get_text()


	def getDownloadInfo(self, source_url, row_id):

		self.log.info("Retrieving item: %s", source_url)


		soup = self.wg.getSoup(source_url, addlHeaders={'Referer': 'http://pururin.us/'})

		if not soup:
			self.log.critical("No download at url %s!", source_url)
			raise IOError("Invalid webpage")

		category, tags = self.getCategoryTags(soup)
		note = self.getNote(soup)

		ret = {}
		ret['file_name'] = self.getFileName(soup)

		read_section = soup.find('i', class_='fa-book')
		read_url = read_section.find_parent("a")

		assert read_url

		spage = urllib.parse.urljoin(self.urlBase, read_url['href'])

		ret["s_page"] = spage


		with self.row_context(dbid=row_id) as row:
			if tags:
				self.update_tags(tags, row=row)
			if note:
				row.additional_metadata = {"note" : note}

			row.last_checked = datetime.datetime.now()
			row.series_name  = category
			ret["source_url"] = row.source_id

		return ret

	def getImage(self, insert_num, imageUrl, referrer):
		content, fName = self.wg.getFileAndName(imageUrl, addlHeaders={'Referer': referrer})

		filen = "{0:04d} - {1:}".format(insert_num, fName)

		self.log.info("retreived image '%s' with a size of %0.3f K", filen, len(content)/1000.0)
		return filen, content

	def getImages(self, dl_info):
		soup = self.wg.getSoup(dl_info['s_page'], addlHeaders={'Referer': dl_info["source_url"]})

		gpages_tag = soup.find('gallery-read')

		assert gpages_tag

		gall_def = json.loads(gpages_tag[':gallery'])


		# I can't imagine google is too enthused about this.
		imgurl_base = 'https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&' + \
			'gadget=a&no_expand=1&resize_w=0&rewriteMime=image/*&url=//api.pururin.io/images/{gid}/{pnum}.png'

		container_page = "https://pururin.io/read/{gid}/{pnum}/release"

		gid    = gall_def['id']
		gpages = gall_def['total_pages']
		images = []

		assert gid
		assert gpages >= 1

		self.log.info("Gallery has %s images", gpages)

		for im_idx in range(1, gpages + 1):
			imgurl    = imgurl_base.format(gid=gid, pnum=im_idx)
			refferrer = container_page.format(gid=gid, pnum=im_idx)
			images.append(self.getImage(im_idx, imgurl, refferrer))

		assert images

		return images


	def get_link(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			row.state  = 'fetching'
			source_url = row.source_id

		try:
			dl_info = self.getDownloadInfo(source_url=source_url, row_id=link_row_id)
			images = self.getImages(dl_info=dl_info)
			file_name = dl_info['file_name']

		except WebRequest.WebGetException:
			self.log.error("Exception!")
			traceback.print_exc()
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False

		assert images

		if not images:
			self.log.error("No images?")
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False


		fileN = file_name+".zip"
		fileN = nt.makeFilenameSafe(fileN)


		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup

			container_dir = os.path.join(settings.puSettings["dlDir"], nt.makeFilenameSafe(row.series_name))
			wholePath = os.path.join(container_dir, row.origin_name)
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




	def setup(self):
		self.wg.stepThroughJsWaf(self.urlBase, titleContains="Pururin")



if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		run.do_fetch_content()

		# todo = run._retreiveTodoLinksFromDB()
		# for link in todo:
		# 	run.getLink(link)

