
if __name__ == "__main__":
	import runStatus
	runStatus.preloadDicts = False

import logging
import psycopg2
import functools
import abc

import threading
import settings
import os
import traceback
import contextlib


from sqlalchemy import or_

import nameTools as nt
import MangaCMS.db as mdb
import MangaCMS.lib.LogMixin
import MangaCMS.lib.MonitorMixin
import MangaCMS.ScrapePlugins.ScrapeExceptions

class MangaScraperDbMixin(MangaCMS.lib.LogMixin.LoggerMixin):


	@abc.abstractmethod
	def plugin_name(self):
		return None

	@abc.abstractmethod
	def plugin_key(self):
		return None

	@abc.abstractmethod
	def is_manga(self):
		return None


	@abc.abstractmethod
	def is_book(self):
		return None

	@abc.abstractmethod
	def is_hentai(self):
		return None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.db = mdb

		assert len([tmp for tmp in [self.is_manga, self.is_book, self.is_hentai] if tmp]) == 1, "You can only be one type"

		if self.is_manga:
			self.shouldCanonize = True
			self.target_table = self.db.MangaReleases
			self.target_tags_table = self.db.MangaTags
		elif self.is_hentai:
			self.shouldCanonize = False
			self.target_table = self.db.HentaiReleases
			self.target_tags_table = self.db.HentaiTags
		elif self.is_book:
			self.shouldCanonize = False
			self.target_table = self.db.BookReleases
			self.target_tags_table = None
		else:
			raise RuntimeError("No mode?")




	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Misc Utilities
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------

	@contextlib.contextmanager
	def row_context(self, *args, **kwargs):
		with self.row_sess_context(*args, **kwargs) as row_tup:
			row, _ = row_tup
			yield row

	@contextlib.contextmanager
	def row_sess_context(self, dbid=None, url=None, limit_by_plugin=True, commit=True):

		assert url or dbid

		with self.db.session_context(commit=commit) as sess:
			row_q = sess.query(self.target_table)

			if limit_by_plugin:
				row_q = row_q.filter(self.target_table.source_site == self.plugin_key)


			if url and dbid:
				raise RuntimeError("Multiple filter parameters (dbid, url) passed to row context manager!")
			elif url:
				row_q = row_q.filter(self.target_table.source_id == url)
			elif dbid:
				row_q = row_q.filter(self.target_table.id == dbid)
			else:
				raise RuntimeError("How did this get executed?")

			yield (row_q.scalar(), sess)

	@contextlib.contextmanager
	def file_row_context(self, *args, **kwargs):
		with self.file_row_sess_context(*args, **kwargs) as row_tup:
			row, _ = row_tup
			yield row

	@contextlib.contextmanager
	def file_row_sess_context(self, dbid, commit=True):

		with self.db.session_context(commit=commit) as sess:
			row_q = sess.query(self.db.ReleaseFile).filter(self.db.ReleaseFile.id == dbid)


			yield (row_q.scalar(), sess)



	def _resetStuckItems(self):
		self.log.info("Resetting stuck downloads in DB")

		with self.db.session_context() as sess:
			res = sess.query(self.target_table)                         \
				.filter(self.target_table.source_site == self.plugin_key) \
				.filter(or_(
					self.target_table.state == 'fetching',
					self.target_table.state == 'processing',
					self.target_table.state == 'missing',
					))                                                  \
				.update({"state" : 'new'})
			self.log.info("Reset updated %s rows!", res)

		self.log.info("Download reset complete")

	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# DB Tools
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


class MangaScraperBase(MangaScraperDbMixin, MangaCMS.lib.LogMixin.LoggerMixin, MangaCMS.lib.MonitorMixin.MonitorMixin):

	def update_tags(self, tags, row=None, dbid=None, url=None):
		assert isinstance(tags, (list, tuple)), "Tags must be a list or tuple"

		assert all([len(tag) >= 2 for tag in tags]),    "All tags must be at least one character long. Bad tags: %s"  % [tag for tag in tags if len(tag) < 2]
		assert all([len(tag) < 90 for tag in tags]),    "All tags must be less then 90 characters long. Bad tags: %s" % [(tag, len(tag)) for tag in tags if len(tag) >= 90]
		assert all([type(tmp) == str for tmp in tags]), "All tags must be a string! Bad tags: %s"                     % [(tag, type(tag)) for tag in tags if type(tag) != str]

		# Short circuit for no tags.
		if not tags:
			return

		if row:
			for tag in tags:
				if (tag.startswith("large_") or tag.startswith("large-")) and 'insertions' not in tag:
					tag= tag.replace("large_", "big-").replace("large-", "big-")
				row.tags.add(tag)
			row_tags = list(row.tags)

		elif dbid or url:
			with self.row_sess_context(dbid=dbid, url=url) as (sess_c, row_c):
				for tag in tags:
					tag_f = sess_c.merge(tag)
					if not tag_f in row.tags:
						row_c.tags.add(tag_f)
				row_tags = list(row_c.tags)
		else:
			raise RuntimeError("You need to pass a filter parameter (row, dbid, url) to update_tags()")

		# Filter against tags.
		if not self.wanted_from_tags(row_tags):
			raise MangaCMS.ScrapePlugins.ScrapeExceptions.UnwantedContentError()

	def wanted_from_tags(self, tags):

		# Skip anything containing a skip tag and not also one of the
		# keep tags.
		have_keep_tags = any(
				[
						    keep_tags in tag
						and tag != 'female-none'
						and tag != 'schoolgirl'
						and tag != 'tomgirl'
						and tag != 'position-cowgirl'
						and tag != 'schoolgirl-uniform'
						and not tag.lower().startswith('artist-')
						and not tag.lower().startswith('fetish-')
						and not tag.lower().startswith('male-')
						and not tag.lower().startswith("parody-")
					for
						tag
					in
						tags
					for
						keep_tags
					in
						settings.tags_keep
				]
			)
		have_skip_tags = any([skip_tag in str(tags) for skip_tag in settings.skipTags])

		if have_skip_tags and not have_keep_tags:
			self.log.warning("Masked item tag (%s).", [skip_tag for skip_tag in settings.skipTags if skip_tag in tags])
			self.log.warning("All item tag (%s).", [skip_tag for skip_tag in settings.skipTags])
			return False

		# print()
		# self.log.info("Masked from tags: %s", [skip_tag for skip_tag in settings.skipTags if skip_tag in tags])
		# self.log.info("Keep tags: %s", [
		# 				tag
		# 			for
		# 				tag
		# 			in
		# 				tags
		# 			for
		# 				keep_tags
		# 			in
		# 				settings.tags_keep
		# 			if
		# 				    keep_tags in tag
		# 				and tag != 'female-none'
		# 				and tag != 'schoolgirl'
		# 				and tag != 'tomgirl'
		# 				and tag != 'position-cowgirl'
		# 				and tag != 'schoolgirl-uniform'
		# 				and not tag.lower().startswith('artist-')
		# 				and not tag.lower().startswith('fetish-')
		# 				and not tag.lower().startswith('male-')
		# 				and not tag.lower().startswith("parody-")
		# 	])
		# self.log.info("All tags: %s", tags)

		return True




if __name__ == "__main__":
	import settings
	class TestClass(MangaScraperDbBase):


		plugin_name = "Wat?"
		logger_path = "Wat?"
		plugin_key = "mk"
		is_manga = True
		def go(self):
			print("Go?")

		def test(self):
			print("Wat?")


	import utilities.testBase as tb

	with tb.testSetup(load=False):
		obj = TestClass()
		print(obj)
		obj.test()
		obj._resetStuckItems()


