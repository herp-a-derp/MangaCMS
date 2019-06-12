


import urllib.parse
import datetime
from dateutil import parser
import calendar
import concurrent.futures

import settings
import MangaCMS.ScrapePlugins.LoaderBase

class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.ASMHentai.Fl"
	plugin_name = "ASMHentai Link Retreiver"
	plugin_key  = "asmh"
	is_manga    = False
	is_hentai   = True
	is_book     = False

	urlBase    = "https://asmhentai.com/"


	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...")
		if not pageOverride:
			pageOverride = 1

		url = "https://asmhentai.com/pag/{}/".format(pageOverride)

		soup = self.wg.getSoup(url, addlHeaders={"Referer" : self.urlBase})

		return soup

	def rowToTags(self, content):
		ret = []
		for item in content.find_all("a"):
			ret.append(item.get_text().strip().lower())
		return ret

	def getInfo(self, itemUrl):
		ret = {'tags' : []}
		soup = self.wg.getSoup(itemUrl)

		del_cnts = soup.find_all("span", class_='gallery_count')
		for bad in del_cnts:
			bad.decompose()

		info_section = soup.find("div", class_='info')

		ret['origin_name'] = info_section.h1.get_text().strip()

		for metarow in soup.find_all("div", class_='tags'):
			sectionname = metarow.h3
			rowdat = metarow.div

			cat = sectionname.get_text().strip()
			if cat == "Uploaded:":
				rowtxt = rowdat.get_text().strip()
				ultime = parser.parse(rowtxt)

				if ultime > datetime.datetime.now():
					self.log.warning("Clamping timestamp to now!")
					ultime = datetime.datetime.now()
				ret['posted_at'] = ultime
			elif cat == "Category:":
				tags = self.rowToTags(rowdat)
				if tags:
					ret["series_name"] = tags[0].title()
				else:
					ret["series_name"] = "Unknown"
			elif cat == "Artists:":
				tags = self.rowToTags(rowdat)
				tags = ["artist "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Groups:":
				tags = self.rowToTags(rowdat)
				tags = ["Group "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Collections:":
				tags = self.rowToTags(rowdat)
				tags = ["Collection "+tag for tag in tags]
				ret['tags'].extend(tags)
				ret['tags'].extend(tags)
			elif cat == "Characters:":
				tags = self.rowToTags(rowdat)
				tags = ["Character "+tag for tag in tags]
				ret['tags'].extend(tags)
			elif cat == "Tags:":
				tags = self.rowToTags(rowdat)
				ret['tags'].extend(tags)


			elif cat == "Parodies:" or cat == "Parody:":
				tags = self.rowToTags(rowdat)
				tags = ["Parody "+tag for tag in tags]

			# Garbage stuff
			elif cat == "Pages":
				pass
			elif cat == "Rating":
				pass
			elif cat == "My Rating":
				pass
			elif cat == "Uploader":
				pass
			elif cat == "Language:":
				tags = self.rowToTags(rowdat)
				tags = ["Language "+tag for tag in tags]
				ret['tags'].extend(tags)

			# The "Download" row has an empty desc
			elif cat == "":
				pass
			else:
				raise RuntimeError("Unknown category tag: '{}' -> '{}'".format(cat, rowdat.prettify()))


		while any(["  " in tag for tag in ret['tags']]):
			ret['tags'] = [tag.replace("  ", " ") for tag in ret['tags']]
		ret['tags'] = [tag.replace(" ", "-") for tag in ret['tags']]
		ret['tags'] = [tag.lower() for tag in ret['tags']]

		# Colons break the tsvector
		ret['tags'] = [tag.replace(":", "-") for tag in ret['tags']]


		# print("Series metadata: ", ret)
		return ret


	def parseItem(self, containerDiv, retag):
		ret = {}
		ret['source_id'] = urllib.parse.urljoin(self.urlBase, containerDiv.a["href"])

		# Do not decend into items where we've already added the item to the DB
		with self.row_context(url=ret['source_id']) as row:
			if row and not retag:
				return

		ret.update(self.getInfo(ret['source_id']))

		if not self.wanted_from_tags(ret['tags']):
			return None

		return ret


	def update_item_tags(self, item):
		self.log.info("Doing tag update")

		# Do not decend into items where we've already added the item to the DB
		with self.row_context(url=item['source_id']) as row:
			if row:
				self.update_tags(item['tags'], row=row)


	def get_feed(self, pageOverride=None, filter_eng=True, time_offset=0, retag=False):

		soup = self.loadFeed(pageOverride)
		divs = soup.find_all("div", class_='preview_item')

		ret = []

		total_items = 0

		for itemDiv in divs:
			# cap = itemDiv.find("div", class_='caption')
			img = itemDiv.find('img', class_='flag')
			if img['src'] == "/images/en.png" or filter_eng != True or retag:
				item = self.parseItem(itemDiv, retag)
				if item:

					item.setdefault('posted_at', datetime.datetime.now())
					ret.append(item)
				total_items += 1

				if retag:
					self.update_item_tags(item)
					ret = []

		self.log.info("Found %s item divs in total", total_items)
		return ret

def process(runner, pageOverride, time_offset, retag=False):
	print("Executing with page offset: pageOverride")
	res = runner.getFeed(pageOverride=pageOverride, filter_eng=False, time_offset=time_offset, retag=retag)
	print("Received %s results!" % len(res))
	runner._processLinksIntoDB(res)


def getHistory(retag=False):
	print("Getting history")
	run = DbLoader()
	with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
		futures = [executor.submit(process, runner=run, pageOverride=x, time_offset=time.time(), retag=retag) for x in range(0, 200)]
		print("Waiting for executor to finish.")
		executor.shutdown()

def test():
	print("Test!")
	run = DbLoader()

	for x in range(25):
		run.do_fetch_feeds(pageOverride=x)

	# print(run.go())
	# print(run)
	# pprint.pprint(run.getFeed())

	# print(run.getInfo("https://asmhentai.com/g/178575/"))

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		# getHistory(retag=True)
		test()
		# run = DbLoader()
		# run.do_fetch_feeds()


