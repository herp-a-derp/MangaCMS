
import time
import abc
import zipfile
import traceback
import os
import os.path
import mimetypes
from concurrent.futures import ThreadPoolExecutor
import magic

import WebRequest

import settings
import datetime
import runStatus
import nameTools as nt

import MangaCMS.cleaner.processDownload
import MangaCMS.ScrapePlugins.MangaScraperBase
import MangaCMS.ScrapePlugins.ScrapeExceptions as ScrapeExceptions
import MangaCMS.util.hashfile as hashfile

def clean_filename(in_filename):
	in_filename = in_filename.replace('.zip .zip', '.zip')
	in_filename = in_filename.replace('.zip.zip', '.zip')
	in_filename = in_filename.replace(' .zip', '.zip')
	in_filename = in_filename.replace('..zip', '.zip')
	in_filename = in_filename.replace('.rar .rar', '.rar')
	in_filename = in_filename.replace('.rar.rar', '.rar')
	in_filename = in_filename.replace(' .rar', '.rar')
	in_filename = in_filename.replace('..rar', '.rar')
	return in_filename


def insertCountIfFilenameExists(fqFName):

	base, ext = os.path.splitext(fqFName)
	loop = 1
	while os.path.exists(fqFName):
		fqFName = "%s - (%d)%s" % (base, loop, ext)
		loop += 1

	return fqFName

def is_in_directory(filepath, directory):
	return os.path.realpath(filepath).startswith(
		os.path.realpath(directory) + os.sep)


def prep_check_fq_filename(fqfilename):
	fqfilename = os.path.abspath(fqfilename)

	# Add a zip extension (if needed). If this is wrong,
	# magic should handle it fine anyways (and the arch processor
	# will probably regnerate the file along the way)
	if not os.path.splitext(fqfilename)[1]:
		fqfilename = fqfilename + ".zip"

	filepath, fileN = os.path.split(fqfilename)
	filepath = clean_filename(filepath)
	fileN = nt.makeFilenameSafe(fileN)

	valid_containers = [settings.pickedDir, settings.baseDir, settings.unlinkedDir, settings.bookDir, settings.h_dir, settings.c_dir, settings.mangaCmsHContext]
	assert any([is_in_directory(filepath, dirc) for dirc in valid_containers
			]), "Saved files must be placed in one of the download paths! File path: %s, valid containers: %s (%s)" % (
				filepath, valid_containers, [is_in_directory(filepath, dirc) for dirc in valid_containers]
				)

	# Create the target container directory (if needed)
	if not os.path.exists(filepath):
		os.makedirs(filepath, exist_ok=True)    # Hurray for race conditions!



	assert os.path.isdir(filepath)


	fqfilename = os.path.join(filepath, fileN)
	fqfilename = insertCountIfFilenameExists(fqfilename)

	return fqfilename


class RetreivalBase(MangaCMS.ScrapePlugins.MangaScraperBase.MangaScraperBase):

	# Abstract class (must be subclassed)
	__metaclass__ = abc.ABCMeta

	plugin_type = "ContentRetreiver"

	itemLimit = 250
	retreival_threads = 1

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.wg = WebRequest.WebGetRobust(logPath=self.logger_path+".Web")
		self.die = False

	@abc.abstractmethod
	def get_link(self, link_row_id):
		pass

	# Provision for a delay. If checkDelay returns false, item is not enqueued
	def checkDelay(self, _):
		return True

	# And for logging in (if needed)
	def setup(self):
		pass

	def processDownload(self, **kwargs):
		assert "plugin_name" not in kwargs, "You can't pass a plugin name to RetreivalBase.processDownload() (%s)" % kwargs
		assert        "pron" not in kwargs, "You can't pass a pron to RetreivalBase.processDownload() (%s)" % kwargs

		kwargs["plugin_name"] = self.plugin_key
		kwargs[       "pron"] = not self.is_manga

		# Never upload hentai, but default to upoading otherwise.
		kwargs[   "doUpload"] = self.is_manga and kwargs.get("doUpload", True)

		return MangaCMS.cleaner.processDownload.processDownload(**kwargs)

	def _retreiveTodoLinksFromDB(self):

		# self.QUERY_DEBUG = True

		self.log.info( "Fetching items from db...",)

		with self.db.session_context() as sess:

			res = sess.query(self.target_table)                            \
				.filter(self.target_table.source_site == self.plugin_key)  \
				.filter(self.target_table.state == 'new')                  \
				.order_by(self.target_table.posted_at.desc())              \
				.all()

			res = [(tmp.id, tmp.posted_at) for tmp in res]

			self.log.info("Query returned %s items", len(res))
		self.log.info( "Done")

		items = []
		for item_row_id, posted_at in res:
			if self.checkDelay(posted_at):
				items.append((item_row_id, posted_at))

		self.log.info( "Have %s new items to retreive in %s Downloader", len(items), self.plugin_key.title())


		items = sorted(items, key=lambda k: k[1], reverse=True)
		if self.itemLimit:
			items = items[:self.itemLimit]

		items = [tmp[0] for tmp in items]

		return items

	def sync_file_tags(self, link_row_id):
		self.log.info("Synchronizing tags with file row")
		with self.row_context(dbid=link_row_id) as row:
			# Occurs if the row got deleted.
			if not row:
				return
			if not row.file:
				return

			release_list = row.file.manga_releases if self.is_manga else row.file.hentai_releases
			file_tag_list = row.file.manga_tags if self.is_manga else row.file.hentai_tags
			if not release_list:
				return

			self.log.info("Found %s release rows associated with file with %s tag(s)", len(release_list), [len(tmp.tags) for tmp in release_list])
			self.log.info("%s tags attached to file row before sync.", len(file_tag_list))

			for release in release_list:
				for tag in release.tags:
					file_tag_list.add(tag)
			self.log.info("File has %s tags after synchronizing", len(file_tag_list))


	def _fetch_link(self, link_row_id):
		try:
			if link_row_id is None:
				self.log.error("Worker received null task! Wat?")
				return
			if self.die:
				self.log.warning("Skipping job due to die flag!")
				return
			if not runStatus.run:
				self.log.info( "Breaking due to exit flag being set")
				return

			with self.row_context(dbid=link_row_id) as row:
				if row.state != 'new':
					self.log.warning("Muliple fetch attemps for the same entry (%s) in plugin %s!", link_row_id, self.plugin_name)
					return

			self.log.info("Fetching content for release with ID: %s", link_row_id)

			status = self.get_link(link_row_id=link_row_id)

			self.sync_file_tags(link_row_id=link_row_id)

			ret1 = None
			if status == 'phash-duplicate':
				ret1 = self.mon_con.incr('phash_dup_items', 1)
			elif status == 'binary-duplicate':
				ret1 = self.mon_con.incr('bin_dup_items', 1)

			# We /always/ send the "fetched_items" count entry.
			# However, the deduped result is only send if the item is actually deduped.
			ret2 = self.mon_con.incr('fetched_items', 1)
			self.log.info("Retreival of release complete. Sending log results:")
			if ret1:
				self.log.info("	-> %s", ret1)
			self.log.info("	-> %s", ret2)


			# Finishing checks
			with self.row_context(dbid=link_row_id) as row:
				if row and row.state == "complete":
					assert row.first_seen    > datetime.datetime.min, "Row first_seen column never set in plugin %s!" % self.plugin_name
					assert row.posted_at     > datetime.datetime.min, "Row posted_at column never set in plugin %s!" % self.plugin_name
					assert row.downloaded_at > datetime.datetime.min, "Row downloaded_at column never set in plugin %s!" % self.plugin_name
					assert row.last_checked  > datetime.datetime.min, "Row last_checked column never set in plugin %s!" % self.plugin_name

		except SystemExit:
			self.die = True
			raise

		except AssertionError:
			self.log.critical("Exception!")
			for line in traceback.format_exc().split("\n"):
				self.log.critical(line)
			self.die = True

			# Reset the download, since failing because a keyboard interrupt is not a remote issue.
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'new'
			raise

		except ScrapeExceptions.UnwantedContentError:
			self.log.info("Row is unwanted! Deleting")
			with self.row_sess_context(dbid=link_row_id) as row_tup:
				row, sess = row_tup
				sess.delete(row)
			return False


		except ScrapeExceptions.LimitedException as e:
			self.log.info("Remote site is rate limiting. Exiting early.")
			self.die = True
			raise e


		except ScrapeExceptions.ContentNotAvailableYetError as e:
			self.log.info("Item seems to be missing content/not available. Deferring.")
			return False

		except KeyboardInterrupt:
			self.log.critical("Keyboard Interrupt!")
			self.log.critical(traceback.format_exc())

			# Reset the download, since failing because a keyboard interrupt is not a remote issue.
			with self.row_context(dbid=link_row_id) as row:
				row.state = 'new'
			raise

		except Exception:
			ret = self.mon_con.incr('failed_items', 1)
			self.log.critical("Sending log result: %s", ret)

			self.log.critical("Exception!")
			for line in traceback.format_exc().split("\n"):
				self.log.critical(line)
			traceback.print_exc()



	def processTodoLinks(self, links):
		if links:

			with ThreadPoolExecutor(max_workers=self.retreival_threads) as executor:

				futures = [executor.submit(self._fetch_link, link) for link in links]

				while futures:
					futures = [tmp for tmp in futures if not (tmp.done() or tmp.cancelled())]
					if not runStatus.run:
						self.log.warning("Cancelling all pending futures")
						for job in futures:
							job.cancel()
						self.log.warning("Jobs cancelled. Exiting executor context.")
						return
					time.sleep(1)





	# ---------------------------------------------------------------------------------------------------------------------------------------------------------
	# Filesystem stuff
	# ---------------------------------------------------------------------------------------------------------------------------------------------------------


	# either locate or create a directory for `seriesName`.
	# If the directory cannot be found, one will be created.
	# Returns {pathToDirectory string}, {HadToCreateDirectory bool}
	def locateOrCreateDirectoryForSeries(self, seriesName):

		if self.shouldCanonize and self.is_manga:
			canonSeriesName = nt.getCanonicalMangaUpdatesName(seriesName)
		else:
			canonSeriesName = seriesName

		safeBaseName = nt.makeFilenameSafe(canonSeriesName)


		if canonSeriesName in nt.dirNameProxy:
			self.log.info("Have target dir for '%s' Dir = '%s'", canonSeriesName, nt.dirNameProxy[canonSeriesName]['fqPath'])
			return nt.dirNameProxy[canonSeriesName]["fqPath"], False
		else:
			self.log.info("Don't have target dir for: %s, full name = %s", canonSeriesName, seriesName)
			targetDir = os.path.join(settings.baseDir, safeBaseName)
			if not os.path.exists(targetDir):
				try:
					os.makedirs(targetDir)
					return targetDir, True

				except FileExistsError:
					# Probably means the directory was concurrently created by another thread in the background?
					self.log.critical("Directory doesn't exist, and yet it does?")
					self.log.critical(traceback.format_exc())
				except OSError:
					self.log.critical("Directory creation failed?")
					self.log.critical(traceback.format_exc())

			else:
				self.log.warning("Directory not found in dir-dict, but it exists!")
				self.log.warning("Directory-Path: %s", targetDir)
				self.log.warning("Base series name: %s", seriesName)
				self.log.warning("Canonized series name: %s", canonSeriesName)
				self.log.warning("Safe canonized name: %s", safeBaseName)
			return targetDir, False

	def _get_existing_file_by_hash(self, sess, file_hash):
		have_row = sess.query(self.db.ReleaseFile)          \
			.filter(self.db.ReleaseFile.fhash == file_hash) \
			.scalar()
		return have_row

	def get_create_file_row(self, sess, row, fqfilename):
		'''
		Given a path to a file, return a row for that file's contents.
		If no row exits, it is created. If a row for another file
		that has exactly matching contents, but a different name
		is found, it is used preferentially.

		Return is a 2-tuple of (file_row, file_path).
		File-path should be guaranteed to point to a valid file.

		Note that the file pointed to by the input parameter fqfilename
		may actually be deleted, if it is found to be a binary duplicate
		of another existing file.
		'''

		# Round-trip via the filesystem because why not
		fhash = hashfile.hash_file(fqfilename)

		have = self._get_existing_file_by_hash(sess, fhash)

		dirpath, filename = os.path.split(fqfilename)
		if have:
			have_fqp = os.path.join(have.dirpath, have.filename)
			if have_fqp == fqfilename:
				self.log.error("Multiple instances of a releasefile created on same on-disk file!")
				self.log.error("File: %s. Row id: %s", have_fqp, row.id)
				raise RuntimeError("Multiple instances of a releasefile created on same on-disk file!")
			if os.path.exists(have_fqp):

				with open(have_fqp, "rb") as fp1:
					fc1 = fp1.read()
				with open(fqfilename, "rb") as fp2:
					fc2 = fp2.read()

				fc1_h = hashfile.hash_bytes(fc1)
				fc2_h = hashfile.hash_bytes(fc2)
				if fc1 != fc2:
					self.log.error("Multiple instances of a releasefile with the same md5, but different contents?")
					self.log.error("File 1: '%s' (%s, %s), Row id: %s", fqfilename, fhash, fc2_h, row.id)
					self.log.error("File 2: '%s' (%s, %s).",            have_fqp, have.fhash, fc1_h)
					raise RuntimeError("Multiple instances of a releasefile with the same md5, but different contents?")

				if fqfilename == have_fqp:
					self.log.warning("Row for file-path already exists?.")
					self.log.warning("Files: '%s', '%s'.", have_fqp, fqfilename)
				elif os.path.exists(have_fqp) and os.path.exists(fqfilename):
					self.log.warning("Duplicate file found by md5sum search. Re-using existing file.")
					self.log.warning("Files: '%s', '%s'.", have_fqp, fqfilename)
					os.unlink(fqfilename)
				else:
					self.log.warning("Duplicate file found by md5sum search, but a file is missing?")
					self.log.warning("Files: '%s', '%s'.", have_fqp, fqfilename)

				row.fileid = have.id
				return have, have_fqp
			else:
				self.log.warning("Duplicate file found by md5sum search, but existing file has been deleted.")
				self.log.warning("Files: '%s', '%s'.", have_fqp, fqfilename)

				have.dirpath = dirpath
				have.filename = filename


				return have, fqfilename

		else:

			new_row = self.db.ReleaseFile(
					dirpath  = dirpath,
					filename = filename,
					fhash    = fhash
				)

			sess.add(new_row)
			sess.flush()

			return new_row, fqfilename

	def save_archive(self, row, sess, fqfilename, file_content):

		fqfilename = prep_check_fq_filename(fqfilename)
		filepath, fileN = os.path.split(fqfilename)
		self.log.info("Complete filepath: %s", fqfilename)

		chop = len(fileN)-4

		while 1:
			try:
				with open(fqfilename, "wb") as fp:
					fp.write(file_content)

				file_row, have_fqp = self.get_create_file_row(sess, row, fqfilename)
				row.fileid = file_row.id

				return have_fqp

			except (IOError, OSError):
				chop = chop - 1
				filepath, fileN = os.path.split(fqfilename)

				fileN = fileN[:chop]+fileN[-4:]
				self.log.warn("Truncating file length to %s characters and re-encoding.", chop)
				fileN = fileN.encode('utf-8','ignore').decode('utf-8')
				fileN = nt.makeFilenameSafe(fileN)
				fqfilename = os.path.join(filepath, fileN)
				fqfilename = insertCountIfFilenameExists(fqfilename)




	def save_image_set(self, row, sess, fqfilename, image_list):

		fqfilename = prep_check_fq_filename(fqfilename)

		self.log.info("Saving to complete filepath: %s", fqfilename)

		filepath, fileN = os.path.split(fqfilename)
		assert len(image_list) >= 1
		chop = len(fileN)-4

		while 1:
			try:
				arch = zipfile.ZipFile(fqfilename, "w")


				self.log.info("Saving %s images to archive %s", len(image_list), fqfilename)
				for imageName, imageContent in image_list:
					self.log.info("	Image: %s (%s bytes)", imageName, len(imageContent))

				#Write all downloaded files to the archive.
				for imageName, imageContent in image_list:
					assert isinstance(imageName, str)
					assert isinstance(imageContent, bytes)

					mtype = magic.from_buffer(imageContent, mime=True)
					if imageName.lower().endswith(".png") and mtype == 'application/octet-stream':
						# So libmagic is somehow misidentifiying pngs as being of type
						# 'application/octet-stream'. Anyways, short circut that specific case.
						pass
					else:
						assert "image" in mtype.lower(), "Image not in mimetype ('%s') of file '%s'?" % (mtype, imageName)

					_, ext = os.path.splitext(imageName)
					fext = mimetypes.guess_extension(mtype)
					if fext == '.jpe':
						fext = ".jpg"
					if ext == '.jpeg':
						ext = ".jpg"
					if fext == '.jpeg':
						fext = ".jpg"

					if not ext:
						self.log.warning("Missing extension in archive file: %s", imageName)
						self.log.warning("Appending guessed file-extension %s", fext)
						imageName += fext
					elif fext != ext:
						self.log.warning("Archive file extension %s mismatches guessed extension: %s", (imageName, ext), fext)
						self.log.warning("Appending guessed file-extension %s", fext)
						imageName += fext


					arch.writestr(imageName, imageContent)
				arch.close()

				file_row, have_fqp = self.get_create_file_row(sess, row, fqfilename)
				row.fileid = file_row.id

				return have_fqp

			except (IOError, OSError):
				traceback.print_exc()


				chop = chop - 1
				filepath, fileN = os.path.split(fqfilename)

				fileN = fileN[:chop]+fileN[-4:]
				self.log.warn("Truncating file length to %s characters and re-encoding.", chop)
				fileN = fileN.encode('utf-8','ignore').decode('utf-8')
				fileN = nt.makeFilenameSafe(fileN)
				fqfilename = os.path.join(filepath, fileN)
				fqfilename = insertCountIfFilenameExists(fqfilename)


	def save_manga_image_set(self, row_id, series_name, chapter_name, image_list, source_name=None):
			dlPath, newDir = self.locateOrCreateDirectoryForSeries(series_name)

			with self.row_context(dbid=row_id) as row:
				row.state = 'processing'
				row.dirstate = 'created_dir' if newDir else "had_dir"


			chapName = chapter_name + (" [%s]" % source_name if source_name else "") + ".zip"
			chapName = chapName.replace("/", " ").replace("\\", " ")
			fqFName = os.path.join(dlPath, chapName)

			self.log.info("Saving item to path: %s", fqFName)

			with self.row_sess_context(dbid=row_id) as row_tup:
				row, sess = row_tup
				fqFName = self.save_image_set(row, sess, fqFName, image_list)

			self.log.info("Processing download")
			if self.is_manga:
				self.processDownload(seriesName = series_name, archivePath = fqFName, doUpload = self.plugin_key == "mdx")
			elif self.is_hentai:
				self.processDownload(seriesName = series_name, archivePath = fqFName, doUpload = False)
			elif self.is_book:
				pass
			else:
				raise RuntimeError("Unknown type!")

			with self.row_context(dbid=row_id) as row:
				row.state         = 'complete'
				row.downloaded_at = datetime.datetime.now()
				row.last_checked  = datetime.datetime.now()
			self.log.info("Download complete!")

	def do_fetch_content(self):
		if hasattr(self, 'setup'):
			self.setup()

		todo = self._retreiveTodoLinksFromDB()
		if not runStatus.run:
			return

		if not todo:
			ret = self.mon_con.incr('fetched_items.count', 0)
			self.log.info("No links to fetch. Sending null result: %s", ret)

		if todo:
			self.processTodoLinks(todo)
		self.log.info("ContentRetreiver for %s has finished.", self.plugin_name)

	def go(self):
		raise ValueError("use do_fetch_content() instead!")
