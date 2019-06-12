
# -*- coding: utf-8 -*-

import os
import os.path

import datetime
import random
import sys
import zipfile
import nameTools as nt

import runStatus
import time
import urllib.request, urllib.parse, urllib.error
import traceback

import settings
import bs4

import MangaCMS.ScrapePlugins.RetreivalBase
import MangaCMS.cleaner.processDownload

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):




	logger_path = "Main.Manga.HBrowse.Cl"
	plugin_name = "H-Browse Content Retreiver"
	plugin_key  = "hb"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "http://www.hbrowse.com/"

	retreivalThreads = 2

	shouldCanonize = False

	def getFileName(self, soup):
		title = soup.find("h1", class_="otitle")
		if not title:
			raise ValueError("Could not find title. Wat?")
		return title.get_text()

	def getCategoryTags(self, soup):
		tables = soup.find_all("table", class_="listTable")

		tags = []


		formatters = {

						'Genre'        : 'Genre',
						'Type'         : '',
						'Setting'      : '',
						'Fetish'       : 'Fetish',
						'Role'         : '',
						'Relationship' : '',
						'Male Body'    : 'Male',
						'Female Body'  : 'Female',
						'Grouping'     : 'Grouping',
						'Scene'        : '',
						'Position'     : 'Position',
						'Artist'       : "Artist"

					}

		ignoreTags = [
						'Length'
					]



		# 'Origin'       : '',  (Category)
		category = "Unknown?"
		title = "None?"
		for table in tables:
			for tr in table.find_all("tr"):
				if len(tr.find_all("td")) != 2:
					continue

				what, values = tr.find_all("td")
				what = what.get_text().strip()

				# print("Row what", what, "values", values.get_text().strip())

				if what in ignoreTags:
					continue

				elif what == "Origin":
					category = values.get_text().strip()

				elif what == "Title":
					title = values.get_text().strip()

					# If cloudflare is fucking shit up, just try to get the title from the title tag.
					if r"[email\xa0protected]" in title or r'[email protected]' in title:
						title = soup.title.get_text().split(" by ")[0]


				elif what in formatters:
					for rawTag in values.find_all("a"):
						tag = " ".join([formatters[what], rawTag.get_text().strip()])
						tag = tag.strip()
						tag = tag.replace("  ", " ")
						tag = tag.replace(" ", "-")
						tags.append(tag)

		# print("title", title)
		# print("Category", category)
		# print("Tags", tags)
		return title, category, tags

	def getGalleryStartPages(self, soup):
		linkTds = soup.find_all("td", class_="listMiddle")

		ret = []

		for td in linkTds:
			url = urllib.parse.urljoin(self.urlBase, td.a['href'])
			ret.append(url)

		return ret

	def get_dl_meta(self, link_row_id):

		with self.row_context(dbid=link_row_id) as row:
			source_url = row.source_id
			row.state = 'fetching'

		try:
			soup = self.wg.getSoup(source_url, addlHeaders={'Referer': 'http://hbrowse.com/'})
		except:
			self.log.critical("No download at url %s! link_row_id = %s", source_url, link_row_id)
			raise IOError("Invalid webpage")

		title, category, tags = self.getCategoryTags(soup)


		with self.row_context(dbid=link_row_id) as row:
			self.update_tags(tags, row=row)

			row.series_name = category
			row.origin_name = title


		startPages = self.getGalleryStartPages(soup)

		ret = {
			"dlLink" : startPages,
			"sourceUrl" : source_url,
		}





		return ret


	def fetchImages(self, linkDict):
		toFetch = {key:0 for key in linkDict["dlLink"]}
		baseUrls = [item for item in linkDict["dlLink"]]
		images = {}
		visited = set()
		bad = 0
		while not all(toFetch.values()):

			# get a random dict element where downloadstate = 0
			thisPage = list(toFetch.keys())[list(toFetch.values()).index(0)]

			soup = self.wg.getSoup(thisPage, addlHeaders={'Referer': linkDict["sourceUrl"]})

			imageTd = soup.find('td', class_='pageImage')

			imageUrl = urllib.parse.urljoin(self.urlBase, imageTd.img["src"])

			imagePath = urllib.parse.urlsplit(imageUrl)[2]
			chapter = imageUrl.split("/")[-2]
			imName = imagePath.split("/")[-1]
			imageFileName = '{c} - {i}'.format(c=chapter, i=imName)

			self.log.info("Using filename '%s'", imageFileName)


			imageData = self.wg.getpage(imageUrl, addlHeaders={'Referer': thisPage})
			images[imageFileName] = imageData

			toFetch[thisPage] = 1
			# Find next page

			nextPageLink = imageTd.a['href']

			nextPageLink = urllib.parse.urljoin(self.urlBase, nextPageLink)


			# Block any cases where the next page url is higher then
			# the baseURLs, so that we don't fetch links back up the
			# hierarchy.
			if nextPageLink != linkDict["sourceUrl"] and not any([nextPageLink in item for item in baseUrls]):

				if not nextPageLink in toFetch:
					toFetch[nextPageLink] = 0
				else:
					print("Already fetched %s" % nextPageLink)
			else:
				print("Not adding %s to fetch queue" % nextPageLink)

			if nextPageLink in visited:
				bad += 1

			if bad > 2:
				break

			visited.add(nextPageLink)



		# Use a dict, and then flatten to a list because we will fetch some items twice.
		# Basically, `http://www.hbrowse.com/{sommat}/c00000` has the same image
		# as  `http://www.hbrowse.com/{sommat}/c00000/00001`, but the strings are not matches.
		images = [(key, value) for key, value in images.items()]
		return images


	def doDownload(self, linkDict, link_row_id):

		images = self.fetchImages(linkDict)

		if not images:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False

		assert len(images) > 2

		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup

			container_dir = os.path.join(settings.hbSettings["dlDir"], nt.makeFilenameSafe(row.series_name))
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
			row.last_checked = datetime.datetime.now()


	def get_link(self, link_row_id):
		try:
			row_meta = self.get_dl_meta(link_row_id)
			self.doDownload(row_meta, link_row_id)
		except urllib.error.URLError:
			self.log.error("Failure retrieving content for link_row_id %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'


class HBrowseRetagger(ContentLoader):

	loggerPath = "Main.Manga.HBrowse.Tag"
	pluginName = "H-Browse Content Re-Tagger"


	def getLink(self, link_row_id):
		try:
			url = self.getDownloadInfo(link_row_id)
		except urllib.error.URLError:
			self.log.error("Failure retrieving content for link_row_id %s", link_row_id)
			self.log.error("Traceback: %s", traceback.format_exc())


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		# run = HBrowseRetagger()
		run = ContentLoader()

		run.do_fetch_content()
