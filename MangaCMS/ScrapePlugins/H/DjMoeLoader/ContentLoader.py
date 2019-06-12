
# -*- coding: utf-8 -*-

import os
import os.path

import datetime
import random
import sys

import nameTools as nt

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4
import logging
import magic
import mimetypes
import WebRequest
import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase

class PageContentError(RuntimeError):
	pass

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):
	log = logging.getLogger("Main.Manga.DjM.Cl")


	logger_path = "Main.Manga.DjM.Cl"
	plugin_name = "DjMoe Content Retreiver"
	plugin_key  = "djm"
	is_manga    = False
	is_hentai   = True
	is_book     = False


	urlBase = "http://doujins.com/"
	shouldCanonize = False


	def getDirAndFName(self, soup):
		title = soup.find("div", class_="folder-title")
		if not title:
			raise PageContentError("Could not find title. Wat?")
		titleSplit = title.get_text().split("»")
		safePath = [nt.makeFilenameSafe(item.strip()) for item in titleSplit]
		fqPath = os.path.join(settings.djSettings["dlDir"], *safePath)
		dirPath, fName = fqPath.rsplit("/", 1)
		self.log.info("dirPath = %s", dirPath)
		self.log.info("fName = %s", fName)
		return dirPath, fName, titleSplit[-1].strip()

	def getDownloadInfo(self, content_id):


		self.log.info("Retrieving metadata for item: %s", content_id)

		ret = {}

		if not content_id.startswith("http"):
			sourcePage = urllib.parse.urljoin(self.urlBase, "/gallery/{gid}".format(gid=content_id))
		else:
			sourcePage = content_id

		soup = self.wg.getSoup(sourcePage)
		if not soup:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, content_id)
			raise PageContentError()

		try:
			dirPath, originName, seriesName = self.getDirAndFName(soup)
		except AttributeError:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, content_id)
			raise PageContentError()

		except ValueError:
			self.log.critical("No download at url %s! SourceUrl = %s", sourcePage, content_id)
			raise PageContentError()

		image_container = soup.find("div", id='image-container')


		ret_link_list = []
		for img_tag in image_container.find_all("img"):
			if img_tag['data-link'] == "/subscribe":
				raise PageContentError("Subscription content!")

			assert img_tag['data-file'], "Missing url for image: %s" % img_tag
			ret_link_list.append((img_tag['data-file'], sourcePage))

		note = soup.find("div", class_="message")
		if note is None or note.string is None:
			note = " "
		else:
			note = nt.makeFilenameSafe(note.string)

		tags = soup.find("li", class_="tag-area")
		tagList = []
		if tags:
			for tag in tags.find_all("a"):
				tag_tmp = tag.get_text()
				tagList.append(tag_tmp.lower().rstrip(", ").lstrip(", ").replace(" ", "-"))

		artist_area = soup.find('div', class_='gallery-artist')
		aList = []
		if artist_area:
			for artist_link in artist_area.find_all("a"):
				a_tag = artist_link.get_text(strip=True)
				aList.append(a_tag)
				a_tag = "artist " + a_tag
				tagList.append(a_tag.lower().rstrip(", ").lstrip(", ").replace(" ", "-"))

		artist = ",".join(aList)

		ret = {
			'artist'        : artist,
			'dirPath'       : dirPath,
			'originName'    : originName,
			'seriesName'    : seriesName,
			'tagList'       : tagList,
			'note'          : note,
			'ret_link_list' : ret_link_list,
		}

		# if not os.path.exists(linkDict["dirPath"]):
		# 	os.makedirs(linkDict["dirPath"])
		# else:
		# 	self.log.info("Folder Path already exists?: %s", linkDict["dirPath"])


		# self.log.info("Folderpath: %s", linkDict["dirPath"])
		# #self.log.info(os.path.join())

		# self.log.debug("Linkdict = ")
		# for key, value in list(linkDict.items()):
		# 	self.log.debug("		%s - %s", key, value)

		return ret


	def getImage(self, imageUrl, referrer, fidx):

		content, fname, mimetype = self.wg.getFileNameMime(imageUrl, addlHeaders={'Referer': referrer})
		if not content:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fext = mimetypes.guess_extension(mimetype)

		# Assume jpeg if we can't figure it out, because it's probably safe.
		if fext == '.a' or not fext or fext == ".jpe":
			fext = ".jpg"

		filename = "{counter} {orig}{ext}".format(
				orig    = fname,
				counter = str(fidx).zfill(4),
				ext     = fext,
			)

		self.log.info("retreived image '%s' with a size of %0.3f K", filename, len(content)/1000.0)
		return filename, content


	def getImages(self, imageurls):

		images = []

		fidx = 1
		for imageurl, referrer in imageurls:
			images.append(self.getImage(imageurl, referrer, fidx))
			fidx += 1

		return images

	def get_link(self, link_row_id):

		images = None

		with self.row_context(dbid=link_row_id) as row:
			source_url = row.source_id
			row.state = 'fetching'

		try:

			dl_info = self.getDownloadInfo(content_id=source_url)

			# ret = {
			# 	'artist'        : artist,
			# 	'dirPath'       : dirPath,
			# 	'originName'    : originName,      -
			# 	'seriesName'    : seriesName,      -
			# 	'tagList'       : tagList,         -
			# 	'note'          : note,            -
			# 	'ret_link_list' : ret_link_list,   -
			# }


			with self.row_context(dbid=link_row_id) as row:
				self.update_tags(dl_info['tagList'], row=row)

				if dl_info['note']:
					row.additional_metadata = {'note' : dl_info['note']}
				row.series_name = dl_info['seriesName']
				row.origin_name = dl_info['originName']
				row.lastUpdate  = datetime.datetime.now()

			images = self.getImages(dl_info['ret_link_list'])


		except WebRequest.WebGetException:
			self.log.info("WebRequest.WebGetException for item ID: %s", link_row_id)
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()
			return False

		except PageContentError:
			self.log.info("PageContentError for item ID: %s", link_row_id)
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
				row.err_str = traceback.format_exc()
			return False

		if not (images and dl_info['seriesName']):
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False


		fileN = dl_info['seriesName']+" - "+dl_info['artist']+".zip"
		fileN = nt.makeFilenameSafe(fileN)

		container_dir = dl_info['dirPath']

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


		delay = random.randint(5, 30)
		self.log.info("Sleeping %s", delay)
		time.sleep(delay)

		return True


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		# run = HBrowseRetagger()
		run = ContentLoader()
		run.do_fetch_content()


