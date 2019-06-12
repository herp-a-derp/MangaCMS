





import traceback
import datetime
import urllib.parse
import time
import calendar
import dateutil.parser
import runStatus
import settings
import os.path

import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.RetreivalBase
import MangaCMS.ScrapePlugins.LoaderBase

import nameTools as nt

class Loader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase,
		MangaCMS.ScrapePlugins.RetreivalBase.RetreivalBase):



	logger_path = "Main.Manga.Yo.Fl"
	plugin_name = "YoManga Scans Link Retreiver"
	plugin_key  = "ym"
	is_manga    = True
	is_hentai   = False
	is_book     = False


	urlBase    = "http://yomanga.co/"
	seriesBase = "http://yomanga.co/reader/directory/%s/"



	def doDownload(self, seriesName, dlurl, chapter_name):

		with self.row_context(url=dlurl) as row:
			if row and row.state != 'new':
				return

		link = {
			"series_name" : seriesName,
			"source_id"   : dlurl,
			'posted_at'   : datetime.datetime.now(),
			'state'       : 'fetching'
		}

		self._process_links_into_db([link])

		try:

			fctnt, fname = self.wg.getFileAndName(dlurl)

		except:
			self.log.error("Unrecoverable error retrieving content %s", (seriesName, dlurl))
			self.log.error("Traceback: %s", traceback.format_exc())

			with self.row_context(url=dlurl) as row:
				row.state = 'error'
			return



		target_dir, new_dir = self.locateOrCreateDirectoryForSeries(seriesName)
		with self.row_context(url=dlurl) as row:
			row.dirstate = 'created_dir' if new_dir else 'had_dir'
			row.origin_name = fname


		fileN = '{series} - {chap} [YoManga].zip'.format(series=seriesName, chap=chapter_name)
		fileN = nt.makeFilenameSafe(fileN)

		fqFName = os.path.join(target_dir, fileN)

		# This call also inserts the file parameters into the row
		with self.row_sess_context(url=dlurl) as row_tup:
			row, sess = row_tup
			fqFName = self.save_archive(row, sess, fqFName, fctnt)

		#self.log.info( filePath)

		with self.row_context(url=dlurl) as row:
			row.state = 'processing'

		self.processDownload(seriesName=seriesName, archivePath=fqFName)


		self.log.info( "Done")
		with self.row_context(url=dlurl) as row:
			row.state = 'complete'
			row.downloaded_at = datetime.datetime.now()
			row.last_checked = datetime.datetime.now()

		return


	def get_link(self, url):
		new = 0
		total = 0


		soup = self.wg.getSoup(url)

		stitle = soup.find("h1", class_='title').get_text().strip()


		chapters = soup.find_all("div", class_='element')
		for chapter in chapters:
			dlurl = chapter.find("div", class_='fleft')
			chp_name = chapter.find("div", class_="title").get_text().strip()
			wasnew = self.doDownload(stitle, dlurl.a['href'], chp_name)
			if wasnew:
				new += 1
			total += 1


		return new, total

	def getSeriesUrls(self):
		ret = set()

		self.wg.stepThroughJsWaf(self.seriesBase % 1, titleContains='Series List')

		page = 1
		while True:
			soup = self.wg.getSoup(self.seriesBase % page)

			new = False

			rows = soup.find_all('div', class_='group')

			for row in rows:
				if row.a['href'] not in ret:
					new = True
					ret.add(row.a['href'])

			page += 1
			if not new:
				break

		self.log.info("Found %s series", len(ret))

		return ret


	def get_feed(self):
		# Stubbed to shut up the base-class
		pass

	def go(self):
		self.log.info( "Loading YoManga Items")


		seriesPages = self.getSeriesUrls()

		tot_new, total_overall = 0, 0

		for item in seriesPages:

			new, total     = self.get_link(item)
			tot_new       += new
			total_overall += total

		self.log.info("Found %s total items, %s of which were new", total_overall, tot_new)
		return []



if __name__ == '__main__':

	# import MangaCMSOld.lib.logSetup
	# MangaCMSOld.lib.logSetup.initLogging()
	# fl = Loader()
	# print("fl", fl)
	# fl.go()

	# urls = fl.getContentForItem('http://yomanga.co/reader/series/brawling_go/')
	# urls = fl.getSeriesUrls()
	# print(urls)


	import utilities.testBase as tb
	with tb.testSetup():

		fl = Loader()
		print("fl", fl)
		fl.go()
		# fl = Loader()
		# print("fl", fl)
		# # fl.go()
		# fl.getSeriesUrls()
		# items = fl.getItemPages('http://mangastream.com/manga/area_d')
		# print("Items")
		# for item in items:
		# 	print("	", item)

