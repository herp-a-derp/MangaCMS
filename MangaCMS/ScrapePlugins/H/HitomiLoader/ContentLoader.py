
# -*- coding: utf-8 -*-

import re

import os
import os.path
import datetime
import urllib.parse
import bs4

import runStatus
runStatus.preloadDicts = False
import nameTools as nt
import settings

import WebRequest

import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase

class ContentLoader(MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):




	logger_path = "Main.Manga.Hitomi.Cl"
	plugin_name = "Hitomi Content Retreiver"
	plugin_key   = "hit"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase = "https://hitomi.la/"

	retreival_threads = 1


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
		if "♀" in tag_raw:
			tag_raw = tag_raw.replace("♀", "")
			tag_raw = "female " + tag_raw
		if "♂" in tag_raw:
			tag_raw = tag_raw.replace("♂", "")
			tag_raw = "male " + tag_raw

		tag = tag_raw.strip()
		while "  " in tag:
			tag = tag.replace("  ", " ")
		tag = tag.strip().replace(" ", "-")
		return tag.lower()

	def getCategoryTags(self, soup):
		tablediv = soup.find("div", class_='gallery-info')
		tagTable = soup.find("table")

		tags = []

		formatters = {
						"series"     : "parody",
						"characters" : "characters",
						"tags"       : "",
					}

		ignoreTags = [
					]

		# print("soup.h2", )

		category = "Unknown?"

		for tr in tagTable.find_all("tr"):
			if len(tr.find_all("td")) != 2:
				continue

			what, values = tr.find_all("td")

			what = what.get_text().strip().lower()
			if what in ignoreTags:
				continue
			elif what == "type":
				category = values.get_text().strip()
				if category == "Manga One-shot":
					category = "=0= One-Shot"
			elif what == "language":

				lang_tag = values.get_text().strip()
				lang_tag = self.format_tag("language " + lang_tag)
				tags.append(lang_tag)

			elif what in formatters:
				for li in values.find_all("li"):
					tag = " ".join([formatters[what], li.get_text()])
					tag = self.format_tag(tag)
					tags.append(tag)

		artist_str = "unknown artist"
		for artist in soup.h2("li"):
			artist_str = artist.get_text()
			atag = "artist " + artist_str
			atag = self.format_tag(atag)
			tags.append(atag)

		# print(category, tags)
		return category, tags, artist_str

	def getDownloadInfo(self, link_row_id):
		with self.row_context(dbid=link_row_id) as row:

			source_url = row.source_id
			# row.state = 'fetching'

		self.log.info("Retrieving item: %s", source_url)


		soup = self.wg.getSoup(source_url, addlHeaders={'Referer': 'https://hitomi.la/'})

		if not soup:
			self.log.critical("No download at url %s!", source_url)
			raise IOError("Invalid webpage")

		gal_section = soup.find("div", class_='gallery')

		category, tags, artist = self.getCategoryTags(gal_section)

		ret = {}

		ret['artist']       = artist
		ret['category']     = category
		ret['title']        = self.getFileName(gal_section)
		ret['gallery_base'] = source_url

		with self.row_context(dbid=link_row_id) as row:
			if row:
				if tags:
					self.update_tags(tags, row=row)
				row.series_name = category
				row.posted_at = datetime.datetime.now()


		read_url = soup.find("a", text=re.compile("Read Online", re.IGNORECASE))
		spage = urllib.parse.urljoin(self.urlBase, read_url['href'])

		ret["spage"] = spage
		return ret

	def getImage(self, imageUrl, referrer):

		content, handle = self.wg.getpage(imageUrl, returnMultiple=True, addlHeaders={'Referer': referrer})
		if not content or not handle:
			raise ValueError("Failed to retreive image from page '%s'!" % referrer)

		fileN = urllib.parse.unquote(urllib.parse.urlparse(handle.geturl())[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup
		self.log.info("retreived image '%s' with a size of %0.3f K", fileN, len(content)/1000.0)
		return fileN, content

	def extract_cdn_subdomain(self, url):
		# var number_of_frontends = 2;
		number_of_frontends = 2
		# function subdomain_from_galleryid(g) {
		#         if (adapose) {
		#                 return '0';
		#         }
		#         return String.fromCharCode(97 + (g % number_of_frontends));
		# }

		# function subdomain_from_url(url, base) {
		#         var retval = 'a';
		#         if (base) {
		#                 retval = base;
		#         }

		#         var r = /\/(\d+)\//;
		#         var m = r.exec(url);
		#         var g;
		#         if (m) {
		#                 g = parseInt(m[1]);
		#         }
		#         if (g) {
		#                 retval = subdomain_from_galleryid(g) + retval;
		#         }

		#         return retval;
		# }

		# function url_from_url(url, base) {
		#         return url.replace(/\/\/..?\.hitomi\.la\//, '//'+subdomain_from_url(url, base)+'.hitomi.la/');
		# }

		chunks = [tmp for tmp in url.split("/") if tmp and all([char in '0123456789' for char in tmp])]

		if len(chunks) != 1:
			raise RuntimeError("Too many (or too few) chunks: '%s'" % chunks)

		g = int(chunks[0])

		subid = chr(97 + (g % number_of_frontends)) + "a"

		return subid


	def getImages(self, fetch_params):

		# print("getImage", fetch_params)

		soup = self.wg.getSoup(fetch_params['spage'], addlHeaders={'Referer': fetch_params["gallery_base"]})

		raw_imgs = soup.find_all('div', class_="img-url")

		imageurls = []


		for div in raw_imgs:
			imgurl = div.get_text().strip()
			# print("ImageURL:", imgurl)
			imgurl = re.sub(r"\/\/..?\.hitomi\.la\/", 'https://{}.hitomi.la/'.format(self.extract_cdn_subdomain(imgurl)), imgurl, flags=re.IGNORECASE)
			# print("ImageURL:", imgurl)
			imageurls.append((imgurl, fetch_params['spage']))
		if not imageurls:
			return []

		images = []


		for imageurl, referrer in imageurls:
			images.append(self.getImage(imageurl, referrer))

		return images


	def get_link(self, link_row_id):
		try:
			link_info = self.getDownloadInfo(link_row_id)
			images = self.getImages(link_info)
			title  = link_info['title']
			artist = link_info['artist']

		except WebRequest.WebGetException:
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'error'
			return False

		if not (images and title):
			return False


		with self.row_sess_context(dbid=link_row_id) as row_tup:
			row, sess = row_tup

			fileN = title+" - "+artist+".zip"
			fileN = nt.makeFilenameSafe(fileN)

			container_dir = os.path.join(settings.hitSettings["dlDir"],
				nt.makeFilenameSafe(row.series_name))

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



	def setup(self):
		self.wg.stepThroughJsWaf(self.urlBase, titleContains="Hitomi")


if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = ContentLoader()
		# run.getDownloadInfo(317486)
		run.do_fetch_content()

