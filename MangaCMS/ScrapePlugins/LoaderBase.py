


import abc
import datetime

import tqdm
import WebRequest

import settings
import nameTools as nt
import MangaCMS.ScrapePlugins.MangaScraperBase
import MangaCMS.ScrapePlugins.ScrapeExceptions as ScrapeExceptions


class LoaderBase(MangaCMS.ScrapePlugins.MangaScraperBase.MangaScraperBase):

	@abc.abstractmethod
	def get_feed(self):
		return None


	plugin_type = "FeedLoader"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.wg = WebRequest.WebGetRobust(logPath=self.logger_path+".Web")

	def setup(self):
		pass

	def _check_keys(self, check_dict):
		keys = set(check_dict.keys())
		allowed = set([
				'state',
				'err_str',
				'source_site',
				'source_id',
				'posted_at',
				'downloaded_at',
				'last_checked',
				'deleted',
				'was_duplicate',
				'phash_duplicate',
				'uploaded',
				'dirstate',
				'origin_name',
				'series_name',
				'additional_metadata',
				'tags',
			])
		bad = keys - allowed
		assert not bad, "Bad key(s) in ret: '%s'!" % bad

		require = set([
				# 'source_site',
			])
		required_missing = require - keys
		assert not required_missing, "Key(s) missing from ret: '%s'!" % required_missing

		assert isinstance(check_dict.get("tags", []), (list, tuple)), "Tags item must be a list!"


	def _process_links_into_db(self, linksDicts):

		self.log.info( "Inserting...")


		newItems = 0
		with self.db.session_context() as sess:
			for link in tqdm.tqdm(linksDicts):

				self._check_keys(link)

				tags = link.pop("tags", [])
				assert isinstance(tags, (list, tuple)), "tags must be a list or tuple!"

				if 'series_name' in link and self.shouldCanonize:
					link["series_name"] = nt.getCanonicalMangaUpdatesName(link["series_name"])

				have = sess.query(self.target_table)                            \
					.filter(self.target_table.source_site == self.plugin_key)     \
					.filter(self.target_table.source_id == link["source_id"]) \
					.scalar()

				if not have:
					newItems += 1
					have = self.target_table(
							state       = 'new',            # Should be set automatically.
							source_site = self.plugin_key,
							first_seen  = datetime.datetime.now(),
							**link
						)

					sess.add(have)

					if newItems % 1000 == 0:
						self.log.info("Added %s rows, doing incremental commit!", newItems)
						sess.commit()

				if have:
					changed = False
					if 'origin_name' in link and have.origin_name != link['origin_name']:
						self.log.info("Updating origin name dur to difference!")
						self.log.info("Old: '%s'", have.origin_name)
						self.log.info("New: '%s'", link['origin_name'])
						have.origin_name = link['origin_name']

						changed = True
					if 'series_name' in link and have.series_name != link['series_name']:
						self.log.info("Updating series name dur to difference!")
						self.log.info("Old: '%s'", have.series_name)
						self.log.info("New: '%s'", link['series_name'])
						have.series_name = link['series_name']
						changed = True

					if changed:
						sess.commit()


				try:
					self.update_tags(tags=tags, row=have)
				except ScrapeExceptions.UnwantedContentError:
					self.log.info("How does something have masked tags on insertion?")
					sess.delete(have)

		if self.mon_con:
			self.mon_con.incr('new_links', newItems)

		self.log.info( "Done (%s new items, %s total)", newItems, len(linksDicts))

		return newItems

	def do_fetch_feeds(self, *args, **kwargs):
		self._resetStuckItems()
		# dat = self.getFeed(list(range(50)))
		self.setup()
		dat = self.get_feed(*args, **kwargs)
		self.log.info("Found %s total items", len(dat))
		self._process_links_into_db(dat)


	def go(self, *args, **kwargs):
		raise RuntimeError("I think you meant to call 'do_fetch_feeds()'")
