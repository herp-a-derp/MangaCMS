# import sys
# sys.path.insert(0,"..")
import os
import os.path
import sys
import tqdm
import gzip
import json
import datetime
import time

import MangaCMS.lib.logSetup
if __name__ == "__main__":
	MangaCMS.lib.logSetup.initLogging()


import runStatus
runStatus.preloadDicts = False

import traceback
import re
import nameTools as nt
import shutil
import settings
import hashlib

from sqlalchemy import or_
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
import sqlalchemy.exc

import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.MangaScraperBase
import MangaCMS.util.hashfile as hashfile


class CleanerBase(MangaCMS.ScrapePlugins.MangaScraperBase.MangaScraperBase):

	# QUERY_DEBUG = True

	def __init__(self, tableKey=None):
		self.tableKey = tableKey
		super().__init__()


	def __delete(self, sess, frow, wanted):



		fqpath = os.path.join(frow.dirpath, frow.filename)

		if not os.path.exists(fqpath):
			self.log.info("Deleting row for missing item")
			sess.delete(frow)
			sess.commit()


		all_tags = [tag for tag in frow.hentai_tags] + [tag for tag in frow.manga_tags]
		for release in frow.hentai_releases:
			reltags = release.tags
			all_tags += reltags

		all_tags = set(all_tags)
		self.log.info("All tags: %s", all_tags)



		tagagg = " ".join([tmp if tmp else "" for tmp in all_tags])
		lcSet = set(tagagg.lower().split(" "))

		keep_tags = [tag for tag in lcSet if any([item in tag for item in wanted])]

		if keep_tags:
			self.log.error("Item had keeptags! Wat?")
			self.log.error("Keeptags: %s (all: %s)", keep_tags, lcSet)
			return

		self.log.info("Deleting rows!")

		for relrow in frow.hentai_releases:
			sess.delete(relrow)

		sess.delete(frow)
		self.log.info("Committing!")
		sess.commit()

		if os.path.exists(fqpath):
			self.log.info("Deleting file %s.", fqpath)
			os.remove(fqpath)


	def cleanJapaneseOnly(self):
		print("cleanJapaneseOnly")

	def cleanCgOnly(self):
		print("cleanCgOnly")

		bad_tags = [r'%language-japanese%', r'%language-日本語%', r'%language-chinese%', r'%language-n/a%',]

		wanted = [tmp.lower() for tmp in settings.tags_keep]

		with self.db.session_context() as sess:
			likes = [self.db.HentaiTags.tag.like(tag) for tag in bad_tags]

			self.log.info("Querying...")
			bad_tags = sess.query(self.db.HentaiTags).filter(or_(*likes)).all()
			self.log.info("Results:")


			for tag in bad_tags:
				self.log.info("Fetching files for tag %s", tag.tag)

				files = tag.release_files.all()
				self.log.info("Found %s files", len(files))

				for file_row in files:
					stags = str(file_row.hentai_tags)
					self.log.info("------------------------------------------------------------------------------")
					keeps = [tmp for tmp in wanted if tmp in stags]

					self.log.info("File row: %s", file_row.filename)
					self.log.info("Tags: %s", file_row.hentai_tags)
					self.log.info("Cat: %s", [row.series_name for row in file_row.hentai_releases])
					self.log.info("Sources: %s", [row.source_site for row in file_row.hentai_releases])
					self.log.info("Extra: %s, %s, %s",
							[row.origin_name         for row in file_row.hentai_releases],
							[row.series_name         for row in file_row.hentai_releases],
							[row.additional_metadata for row in file_row.hentai_releases],
							)
					would_keep = len(keeps)
					if would_keep:
						self.log.info("Would keep: %s (keeps: %s)", would_keep, keeps)
					else:
						self.log.warning("Would keep: %s", would_keep)
						self.__delete(sess, file_row, wanted)


	def cleanTags(self):
		print("cleanCgOnly")

		with self.db.session_context() as sess:

			self.log.info("Querying...")
			bad_tags = sess.query(self.db.HentaiTags).filter(self.db.HentaiTags.tag.like('large_%')).all()
			self.log.info("Results:")


			for tag in bad_tags:
				if 'insertions' in tag.tag:
					continue
				self.log.info("Fetching files for tag %s", tag.tag)

				files = tag.release_files.all()
				self.log.info("Found %s files", len(files))
				releases = tag.hentai_releases.all()
				self.log.info("Found %s releases", len(releases))
				for release in tqdm.tqdm(releases):
					bad = [tmp for tmp in release.tags if (tmp.startswith("large_") or tmp.startswith("large-")) and 'insertions' not in tmp]
					rep = [tmp.replace("large_", "big-").replace("large-", "big-") for tmp in release.tags if (tmp.startswith("large_") or tmp.startswith("large-")) and 'insertions' not in tmp]
					# print(release.tags)
					if bad and rep:
						for badt in bad:
							release.tags.remove(badt)
						for good in rep:
							release.tags.add(good)


				for release in tqdm.tqdm(files):
					bad = [tmp for tmp in release.hentai_tags if (tmp.startswith("large_") or tmp.startswith("large-")) and 'insertions' not in tmp]
					rep = [tmp.replace("large_", "big-").replace("large-", "big-") for tmp in release.hentai_tags if (tmp.startswith("large_") or tmp.startswith("large-")) and 'insertions' not in tmp]
					# print(release.hentai_tags)
					if bad and rep:
						for badt in bad:
							release.hentai_tags.remove(badt)
						for good in rep:
							release.hentai_tags.add(good)


				self.log.info("Committing...")
				sess.commit()


	def cleanYaoiOnly(self):
		print("cleanYaoiOnly")

		bad_tags = [
			'yaoi',
			'male-yaoi',
			'guys-only',
			'males-only',
			'male-males-only',
			'male-guys-only',
			'trap-yaoi',
		]

		releases = set()
		with self.db.session_context() as sess:
			bad = sess.query(self.db.HentaiTags) \
				.filter(or_(
						*(self.db.HentaiTags.tag.like(tag) for tag in bad_tags)
					)).all()


			self.log.info("Found %s tags to process", len(bad))

			for row in tqdm.tqdm(bad):
				for release in tqdm.tqdm(row.hentai_releases.all()):
					if release.id not in releases:
						releases.add(release.id)

		self.log.info("")
		self.log.info("Found %s items to examine", len(releases))

		releases = list(releases)
		releases.sort(reverse=True)

		for relid in tqdm.tqdm(releases):
			with self.row_sess_context(dbid=relid, limit_by_plugin=False) as (row, sess):

				if not row:
					continue
				if row.last_checked < datetime.datetime.now() - datetime.timedelta(days=7):
					continue



				ftags = set(row.file.hentai_tags)
				atags = set() | ftags
				for a_row in row.file.hentai_releases:
					for tag in a_row.tags:
						atags.add(tag)


				if not self.wanted_from_tags(atags):
					self.log.info("Deleting %s series release rows with tags: %s", len(row.file.hentai_releases), atags)
					for bad_rel in row.file.hentai_releases:
						sess.delete(bad_rel)
					sess.delete(row.file)

					fqp = os.path.join(row.file.dirpath, row.file.filename)
					self.log.info("Deleting file: '%s'", fqp)
					os.unlink(fqp)

	def syncHFileTags(self):
		with self.db.session_context() as sess:
			file_rows = sess.query(self.db.ReleaseFile.id).all()

		file_rows.sort(reverse=True)

		for relid, in tqdm.tqdm(file_rows):

			with self.db.session_context(commit=True) as sess:
				row_q = sess.query(self.db.ReleaseFile)     \
					.options(joinedload("hentai_releases")) \
					.filter(self.db.ReleaseFile.id == relid)

				row = row_q.scalar()
				if row:


					atags = set()
					for a_row in row.hentai_releases:
						for tag in a_row.tags:
							atags.add(tag)

					missing = set()
					for tag in atags:
						if tag not in row.hentai_tags:
							row.hentai_tags.add(tag)
							missing.add(tag)

					if missing:
						self.log.info("Missing tags from row %s -> %s", row.id, missing)


	def refetch_missing_tags(self):
		with self.db.session_context() as sess:
			self.log.info("Loading from DB with join")
			file_rows = sess.query(self.db.HentaiReleases) \
				.order_by(desc(self.db.HentaiReleases.id)) \
				.options(joinedload('tags_rel')) \
				.all()

			self.log.info("Rows loaded. Processing.")

			for row in tqdm.tqdm(file_rows):
				try:
					if row.state != 'new' and not row.tags:
						print(row, row.source_site, row.tags)
						row.state = 'new'
						sess.commit()

				except sqlalchemy.exc.InvalidRequestError:
					print("InvalidRequest error!")
					sess.rollback()
					traceback.print_exc()
				except sqlalchemy.exc.OperationalError:
					print("InvalidRequest error!")
					sess.rollback()
				except sqlalchemy.exc.IntegrityError:
					print("[upsertRssItems] -> Integrity error!")
					traceback.print_exc()
					sess.rollback()


	def findIfMigrated(self, filePath):
		dirPath, fileName = os.path.split(filePath)

		series = dirPath.split("/")[-1]
		series = nt.getCanonicalMangaUpdatesName(series)
		otherDir = nt.dirNameProxy[series]

		if not otherDir["fqPath"]:
			return False
		if otherDir["fqPath"] == dirPath:
			return False

		newPath = os.path.join(otherDir["fqPath"], fileName)
		if os.path.exists(newPath):
			print("File moved!")
			return otherDir["fqPath"]

		return False

	def resetMissingDownloads(self):


		if not nt.dirNameProxy.observersActive():
			nt.dirNameProxy.startDirObservers()


		with self.db.session_context() as sess:
			file_rows = sess.query(self.target_table) \
				.order_by(desc(self.target_table.id)) \
				.options(joinedload('file')) \
				.all()

			self.log.info("Ret %s", len(file_rows))

			loops = 0
			for row in tqdm.tqdm(file_rows):
				if not row.file:
					# self.log.info("No file: %s, %s, %s", row.state, row.source_site, row.source_id)
					if row.state == 'error':
						sess.delete(row)
						sess.commit()
					continue


				filePath = os.path.join(row.file.dirpath, row.file.filename)

				if not os.path.exists(filePath):
					migPath = self.findIfMigrated(filePath)
					if not migPath:
						self.log.info("Resetting download for %s, source=%s", filePath, row.source_site)
						row.state = 'new'

					else:
						self.log.info("Moved!")
						self.log.info("		Old = '%s'" % filePath)
						self.log.info("		New = '%s'" % migPath)
						# self.updatePath(dbId, migPath, cur)

				loops += 1
				if loops % 1000 == 0:
					self.log.info("Incremental Commit!")
					sess.commit()


	def check_file_hashes(self):
		self.log.info("Check file hashes!")
		bad_items = []
		try:
			with self.db.session_context() as sess:
				self.log.info("Loading file listing from db!")
				files = sess.query(self.db.ReleaseFile).order_by(desc(self.db.ReleaseFile.id)).all()
				self.log.info("Found %s files to scan", len(files))
				sess.commit()
				for have in tqdm.tqdm(files):
					have_fqp = os.path.join(have.dirpath, have.filename)
					if not os.path.exists(have_fqp):
						self.log.error("File missing: %s", have_fqp)
						bad_items.append(("missing", have.id, have_fqp))
						continue

					item_hash = hashfile.hash_file(have_fqp)

					if item_hash != have.fhash:
						self.log.error("File hash doesn't match file: %s (%s, %s)", have_fqp, item_hash, have.fhash)
						bad_items.append(("mismatch", have.id, have_fqp))

		finally:
			with open("mismatches.json", "w") as fp:
				json.dump(bad_items, fp, indent=4)
			for item in bad_items:
				self.log.info("Failed: %s", item)


	# # STFU, abstract base class
	def go(self):
		pass

class MCleaner(CleanerBase):
	logger_path = "Main.Mc"
	tableName  = "MangaItems"
	is_manga   = True
	is_hentai  = False
	is_book    = False
	plugin_name = "None"
	plugin_key   = "None"
	plugin_type = 'Utility'

class BCleaner(CleanerBase):
	logger_path = "Main.Mc"
	tableName  = "MangaItems"
	is_manga   = False
	is_hentai  = False
	is_book    = True
	plugin_name = "None"
	plugin_key   = "None"
	plugin_type = 'Utility'


class HCleaner(CleanerBase):
	logger_path = "Main.Hc"
	is_manga   = False
	is_hentai  = True
	is_book    = False
	plugin_name = "None"
	plugin_key   = "None"
	plugin_type = 'Utility'


if __name__ == "__main__":
	import MangaCMS.lib.logSetup
	MangaCMS.lib.logSetup.initLogging()