

import pprint
import datetime

import urllib.parse
import time

import calendar
import parsedatetime

import settings
import MangaCMS.ScrapePlugins.LoaderBase

class NotEnglishException(RuntimeError): pass

class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):


	logger_path = "Main.Manga.Hentai2Read.Fl"
	plugin_name = "Hentai2Read Link Retreiver"
	plugin_key  = "h2r"
	is_manga    = False
	is_hentai   = True
	is_book     = False



	urlBase    = "https://hentai2read.com/"



	def loadFeed(self, pageOverride=None):
		self.log.info("Retrieving feed content...")
		if not pageOverride:
			pageOverride = 1

		url = "https://hentai2read.com/hentai-list/all/any/all/last-updated/{}/".format(pageOverride)

		soup = self.wg.getSoup(url, addlHeaders={"Referer" : self.urlBase})

		return url, soup


	def process_row(self, row_name, row_content):
		ret = []

		tag_buttons = row_content.find_all('a', class_='tagButton')

		tag_buttons = [tmp for tmp in tag_buttons if tmp.get_text(strip=True) != "-"]

		if row_name == 'Parody':
			for button in tag_buttons:
				ret.append("parody " + button.get_text(strip=True))

		elif row_name == 'Ranking':
			pass
		elif row_name == 'Status':
			pass
		elif row_name == 'Rating':
			pass
		elif row_name == 'View':
			pass

		elif row_name == 'Storyline':
			pass

		elif row_name == 'Release Year':
			for button in tag_buttons:
				ret.append("release year " + button.get_text(strip=True))
		elif row_name == 'Author':
			for button in tag_buttons:
				ret.append("author " + button.get_text(strip=True))
		elif row_name == 'Artist':
			for button in tag_buttons:
				ret.append("artist " + button.get_text(strip=True))
		elif row_name == 'Category':
			for button in tag_buttons:
				ret.append(button.get_text(strip=True))
		elif row_name == 'Content':
			for button in tag_buttons:
				ret.append(button.get_text(strip=True))
		elif row_name == 'Character':
			for button in tag_buttons:
				if button.get('href', "Wat").startswith("http"):
					ret.append("character " + button.get_text(strip=True))
		elif row_name == 'Language':
			if row_content.get_text(strip=True) != "English":
				raise NotEnglishException("Language is not english: %s" %  row_content.get_text(strip=True))
			else:
				ret.append("language english")

		else:
			self.log.error("Unknown tag: '%s'", row_name)
			self.log.error("%s", row_content)
			raise RuntimeError("Unknown category tag: '{}' -> '{}'".format(row_name, row_content.prettify()))

		return ret

	def getInfo(self, soup):
		meta_list = soup.find("ul", class_='list')

		meta_dict = {
				'tags'       : [],
				"series_name" : None,
			}
		for list_entry in meta_list.find_all("li"):
			if list_entry.get('class', None) == ['text-muted']:
				sname = list_entry.get_text(strip=True)
				if sname == "-":
					sname = None
				meta_dict["series_name"] = sname

			elif list_entry.b:
				item_name = list_entry.b.get_text(strip=True)
				list_entry.b.decompose()

				meta_dict['tags'].extend(self.process_row(item_name, list_entry))


			else:
				if list_entry.get_text(strip=True):
					self.log.error("Missing heading in section")
					self.log.error("%s", list_entry)


		if meta_dict['series_name'] is None:
			header_div = soup.find("section", class_='content')
			titletag = header_div.find('h3', class_='block-title')
			if titletag.small:
				titletag.small.decompose()

			meta_dict['series_name'] = titletag.get_text(strip=True)

		while any(["  " in tag for tag in meta_dict['tags']]):
			meta_dict['tags'] = [tag.replace("  ", " ") for tag in meta_dict['tags']]
		meta_dict['tags'] = [tag.replace(" ", "-") for tag in meta_dict['tags']]
		meta_dict['tags'] = [tag.lower() for tag in meta_dict['tags']]


		while any(["--" in tag for tag in meta_dict['tags']]):
			meta_dict['tags'] = [tag.replace("--", "-") for tag in meta_dict['tags']]

		# Colons break the tsvector
		meta_dict['tags'] = [tag.replace(":", "-") for tag in meta_dict['tags']]


		return meta_dict


	def parseItem(self, itemurl, refurl):
		ret = []

		soup = self.wg.getSoup(itemurl, addlHeaders={"Referer" : refurl})

		series_meta = self.getInfo(soup)

		if not self.wanted_from_tags(series_meta['tags']):
			return None

		chap_list = soup.find("ul", class_='nav-chapters')

		if not chap_list:
			return ret

		for chap in chap_list.find_all('li', recursive=False):

			bad = chap.find('a', class_='btn-circle')
			if bad:
				bad.decompose()

			chap_d = {key : val for key, val in series_meta.items()}

			chap_d['source_id'] = chap.a['href']

			dateinfo = chap.a.small.get_text()
			chap.a.small.decompose()

			timestr = dateinfo.split(" on ")[-1].strip()

			itemDate, status = parsedatetime.Calendar().parse(timestr)

			if status >= 1:
				chap_d['posted_at'] = datetime.datetime(*itemDate[:6])
			else:
				self.log.warning("Parsing relative date '%s' failed (%s). Using current timestamp.", timestr, status)
				chap_d['posted_at'] = datetime.datetime.now()



			if chap_d['series_name'] is None:
				chap_d['origin_name'] = chap.a.get_text(strip=True)
				chap_d["series_name"] = chap.a.get_text(strip=True)
			else:
				chap_d["origin_name"] = chap_d['series_name'] + " – " + chap.a.get_text(strip=True)

			# assert not chap_d["series_name"].startswith("1"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("2"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("3"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("4"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("5"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("6"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("7"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("8"), "Bad series name: '%s'" % chap_d["series_name"]
			# assert not chap_d["series_name"].startswith("9"), "Bad series name: '%s'" % chap_d["series_name"]

			ret.append(chap_d)


		self.log.info("Found %s chapters on item page", len(ret))


		return ret


	def get_feed(self, pageOverride=None):

		refurl, soup = self.loadFeed(pageOverride)


		divs = soup.find_all("div", class_='img-container')

		ret = []

		for itemDiv in divs:
			series_page =  urllib.parse.urljoin(self.urlBase, itemDiv.h2.parent["href"])
			chapters = self.parseItem(series_page, refurl)
			if chapters:
				ret.extend(chapters)

		return ret

def process(runner, pageOverride):
	print("Executing with page offset: pageOverride")
	runner.do_fetch_feeds(pageOverride=pageOverride)


def getHistory():
	import concurrent.futures
	print("Getting history")
	run = DbLoader()
	with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
		futures = [executor.submit(process, runner=run, pageOverride=x) for x in range(0, 410)]
		print("Waiting for executor to finish.")
		executor.shutdown()

def test():
	print("Test!")
	run = DbLoader()

	dat = run.get_feed()
	print(dat)
	# print(run.go())
	# print(run)
	# pprint.pprint(run.getFeed())

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):
		getHistory()
		# test()

		# run = DbLoader()
		# run.do_fetch_feeds()
