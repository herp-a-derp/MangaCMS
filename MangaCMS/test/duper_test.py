

import unittest
# import os
# print("CWD:", os.getcwd())

# import pdb
# pdb.set_trace()

import MangaCMS.lib.logSetup
import MangaCMS.cleaner.processDownload
from MangaCMS import db as mdb
from MangaCMS.db import db_models as db_models

import settings
assert "test" in settings.NEW_DATABASE_DB_NAME.lower(), "Running tests on non-test database!"

class TestSequenceFunctions(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def setUp(self):
		# print("Doing Setup!")
		MangaCMS.lib.logSetup.DISABLE_REENTRANT_WARNING=True
		MangaCMS.lib.logSetup.initLogging(logToDb=False)
		self.addCleanup(self.dropDatabase)

	def base_setup(self):
		with mdb.session_context() as sess:
			f1 = db_models.ReleaseFile(
				dirpath  = "lol1",
				filename = "lol2",
				fhash    = "lol3",
				)
			f2 = db_models.ReleaseFile(
				dirpath  = "wat1",
				filename = "wat2",
				fhash    = "wat3",
				)

			sess.add(f1)
			sess.add(f2)
			sess.flush()
			# print(f1.id)
			# print(f2.id)

			f1.hentai_tags.add("t1")
			f1.hentai_tags.add("t2")
			f1.hentai_tags.add("t3")
			f1.manga_tags.add("t4")
			f1.manga_tags.add("t5")
			f1.manga_tags.add("t6")

			f2.hentai_tags.add("t7")
			f2.hentai_tags.add("t8")
			f2.hentai_tags.add("t9")
			f2.manga_tags.add("t10")
			f2.manga_tags.add("t11")
			f2.manga_tags.add("t12")

			f1id = f1.id
			f2id = f2.id

		with mdb.session_context() as sess:
			r1 = db_models.MangaReleases(
				source_site = 'test',
				source_id   = 'r1',
				fileid      = f1id,
				)

			r2 = db_models.MangaReleases(
				source_site = 'test',
				source_id   = 'r2',
				fileid      = f1id,
				)

			r3 = db_models.MangaReleases(
				source_site = 'test',
				source_id   = 'r3',
				fileid      = f2id
				)

			r4 = db_models.MangaReleases(
				source_site = 'test',
				source_id   = 'r4',
				fileid      = f2id
				)
			sess.add(r1)
			sess.add(r2)
			sess.add(r3)
			sess.add(r4)

			r1.tags.add("m_r_t1")
			r1.tags.add("m_r_t2")
			r1.tags.add("m_r_t3")
			r1.tags.add("m_r_t4")
			r1.tags.add("m_r_t5")
			r1.tags.add("m_r_t6")

			r2.tags.add("m_r_t7")
			r2.tags.add("m_r_t8")
			r2.tags.add("m_r_t9")
			r2.tags.add("m_r_t10")
			r2.tags.add("m_r_t11")
			r2.tags.add("m_r_t12")

			r3.tags.add("m_r_t1")
			r3.tags.add("m_r_t2")
			r3.tags.add("m_r_t3")
			r3.tags.add("m_r_t4")
			r3.tags.add("m_r_t5")
			r3.tags.add("m_r_t6")

			r4.tags.add("m_r_t7")
			r4.tags.add("m_r_t8")
			r4.tags.add("m_r_t9")
			r4.tags.add("m_r_t10")
			r4.tags.add("m_r_t11")
			r4.tags.add("m_r_t12")

		with mdb.session_context() as sess:
			r5 = db_models.HentaiReleases(
				source_site = 'test',
				source_id   = 'r5',
				fileid      = f1id,
				)

			r6 = db_models.HentaiReleases(
				source_site = 'test',
				source_id   = 'r6',
				fileid      = f1id,
				)

			r7 = db_models.HentaiReleases(
				source_site = 'test',
				source_id   = 'r7',
				fileid      = f2id
				)

			r8 = db_models.HentaiReleases(
				source_site = 'test',
				source_id   = 'r8',
				fileid      = f2id
				)
			sess.add(r5)
			sess.add(r6)
			sess.add(r7)
			sess.add(r8)

			r5.tags.add("h_r_t1")
			r5.tags.add("h_r_t2")
			r5.tags.add("h_r_t3")
			r5.tags.add("h_r_t4")
			r5.tags.add("h_r_t5")
			r5.tags.add("h_r_t6")

			r6.tags.add("h_r_t7")
			r6.tags.add("h_r_t8")
			r6.tags.add("h_r_t9")
			r6.tags.add("h_r_t10")
			r6.tags.add("h_r_t11")
			r6.tags.add("h_r_t12")

			r7.tags.add("h_r_t1")
			r7.tags.add("h_r_t2")
			r7.tags.add("h_r_t3")
			r7.tags.add("h_r_t4")
			r7.tags.add("h_r_t5")
			r7.tags.add("h_r_t6")

			r8.tags.add("h_r_t7")
			r8.tags.add("h_r_t8")
			r8.tags.add("h_r_t9")
			r8.tags.add("h_r_t10")
			r8.tags.add("h_r_t11")
			r8.tags.add("h_r_t12")

		with mdb.session_context() as sess:
			f1 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='lol3').one()
			f2 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='wat3').one()

			self.assertEqual(set(f1.hentai_tags), set(["t1", "t2", "t3"]))
			self.assertEqual(set(f1.manga_tags),  set(["t4", "t5", "t6"]))
			self.assertEqual(set(f2.hentai_tags), set(["t7", "t8", "t9"]))
			self.assertEqual(set(f2.manga_tags),  set(["t10", "t11", "t12"]))


			f1_h_ids = [tmp.source_id for tmp in f1.hentai_releases]
			f1_m_ids = [tmp.source_id for tmp in f1.manga_releases]
			f2_h_ids = [tmp.source_id for tmp in f2.hentai_releases]
			f2_m_ids = [tmp.source_id for tmp in f2.manga_releases]

			self.assertEqual(set(f1_h_ids), set(['r5', 'r6']))
			self.assertEqual(set(f1_m_ids), set(['r1', 'r2']))
			self.assertEqual(set(f2_h_ids), set(['r7', 'r8']))
			self.assertEqual(set(f2_m_ids), set(['r3', 'r4']))

		with mdb.session_context() as sess:

			r1 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r1') \
				.one()
			r2 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r2') \
				.one()
			r3 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r3') \
				.one()
			r4 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r4') \
				.one()

			r5 = sess.query(db_models.HentaiReleases) \
				.filter(db_models.HentaiReleases.source_site=='test') \
				.filter(db_models.HentaiReleases.source_id=='r5') \
				.one()
			r6 = sess.query(db_models.HentaiReleases) \
				.filter(db_models.HentaiReleases.source_site=='test') \
				.filter(db_models.HentaiReleases.source_id=='r6') \
				.one()
			r7 = sess.query(db_models.HentaiReleases) \
				.filter(db_models.HentaiReleases.source_site=='test') \
				.filter(db_models.HentaiReleases.source_id=='r7') \
				.one()
			r8 = sess.query(db_models.HentaiReleases) \
				.filter(db_models.HentaiReleases.source_site=='test') \
				.filter(db_models.HentaiReleases.source_id=='r8') \
				.one()

			r1_t = set(r1.tags)
			r2_t = set(r2.tags)
			r3_t = set(r3.tags)
			r4_t = set(r4.tags)
			r5_t = set(r5.tags)
			r6_t = set(r6.tags)
			r7_t = set(r7.tags)
			r8_t = set(r8.tags)

			self.assertEqual(r1_t, {'m_r_t4', 'm_r_t2', 'm_r_t5', 'm_r_t1', 'm_r_t6', 'm_r_t3'})
			self.assertEqual(r2_t, {'m_r_t12', 'm_r_t8', 'm_r_t11', 'm_r_t7', 'm_r_t9', 'm_r_t10'})
			self.assertEqual(r3_t, {'m_r_t4', 'm_r_t2', 'm_r_t5', 'm_r_t1', 'm_r_t6', 'm_r_t3'})
			self.assertEqual(r4_t, {'m_r_t12', 'm_r_t8', 'm_r_t11', 'm_r_t7', 'm_r_t9', 'm_r_t10'})
			self.assertEqual(r5_t, {'h_r_t6', 'h_r_t4', 'h_r_t2', 'h_r_t5', 'h_r_t3', 'h_r_t1'})
			self.assertEqual(r6_t, {'h_r_t9', 'h_r_t10', 'h_r_t12', 'h_r_t11', 'h_r_t7', 'h_r_t8'})
			self.assertEqual(r7_t, {'h_r_t6', 'h_r_t4', 'h_r_t2', 'h_r_t5', 'h_r_t3', 'h_r_t1'})
			self.assertEqual(r8_t, {'h_r_t9', 'h_r_t10', 'h_r_t12', 'h_r_t11', 'h_r_t7', 'h_r_t8'})


	def dropDatabase(self):
		# print("Cleanup!")
		with mdb.session_context() as sess:
			# First, delete the link table entries
			sess.query(db_models.manga_files_tags_link).delete(synchronize_session=False)
			sess.query(db_models.manga_releases_tags_link).delete(synchronize_session=False)
			sess.query(db_models.hentai_files_tags_link).delete(synchronize_session=False)
			sess.query(db_models.hentai_releases_tags_link).delete(synchronize_session=False)


			# Delete the releases/tags
			sess.query(db_models.MangaReleases).delete()
			sess.query(db_models.HentaiReleases).delete()
			sess.query(db_models.MangaTags).delete()
			sess.query(db_models.HentaiTags).delete()

			# Finally, the files
			sess.query(db_models.ReleaseFile).delete()


	def test_basic_1(self):
		self.base_setup()

	def test_tag_reuse(self):
		self.base_setup()

		with mdb.session_context() as sess:
			m_tag_c_1 = sess.query(db_models.MangaTags).count()
			h_tag_c_1 = sess.query(db_models.HentaiTags).count()

		with mdb.session_context() as sess:
			f2 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='wat3').one()
			f2.hentai_tags.add("t1")
			f2.hentai_tags.add("t2")
			f2.hentai_tags.add("t3")
			f2.manga_tags.add("t4")
			f2.manga_tags.add("t5")
			f2.manga_tags.add("t6")

		with mdb.session_context() as sess:
			m_tag_c_2 = sess.query(db_models.MangaTags).count()
			h_tag_c_2 = sess.query(db_models.HentaiTags).count()

		self.assertEqual(m_tag_c_1, m_tag_c_2)
		self.assertEqual(h_tag_c_1, h_tag_c_2)

	def test_file_relink_fid(self):
		self.base_setup()

		m_dlproc = MangaCMS.cleaner.processDownload.MangaProcessor()
		h_dlproc = MangaCMS.cleaner.processDownload.HentaiProcessor()
		with mdb.session_context() as sess:

			f2 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='wat3').one()

			a_r3 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r3') \
				.one()
			a_r4 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r4') \
				.one()

			self.assertEqual(f2.id, a_r3.fileid)
			self.assertEqual(f2.id, a_r4.fileid)

		m_dlproc._create_or_update_file_entry_path("wat1/wat2", "lol1/lol2")

		with mdb.session_context() as sess:

			f1 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='lol3').one()

			b_r3 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r3') \
				.one()
			b_r4 = sess.query(db_models.MangaReleases) \
				.filter(db_models.MangaReleases.source_site=='test') \
				.filter(db_models.MangaReleases.source_id=='r4') \
				.one()

			self.assertEqual(f1.id, b_r3.fileid)
			self.assertEqual(f1.id, b_r4.fileid)


	def test_file_relink_tags(self):
		self.base_setup()

		m_dlproc = MangaCMS.cleaner.processDownload.MangaProcessor()
		h_dlproc = MangaCMS.cleaner.processDownload.HentaiProcessor()
		with mdb.session_context() as sess:

			f2 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='wat3').one()
			f3 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='lol3').one()

			f2_m_tags = set(f2.manga_tags)
			f2_h_tags = set(f2.hentai_tags)
			f3_m_tags = set(f3.manga_tags)
			f3_h_tags = set(f3.hentai_tags)

			self.assertEqual(f2_m_tags, {'t11', 't12', 't10'} )
			self.assertEqual(f2_h_tags, {'t9', 't8', 't7'} )
			self.assertEqual(f3_m_tags, {'t5', 't6', 't4'} )
			self.assertEqual(f3_h_tags, {'t1', 't2', 't3'})


		m_dlproc._create_or_update_file_entry_path("wat1/wat2", "lol1/lol2")

		with mdb.session_context() as sess:

			f1 = sess.query(db_models.ReleaseFile).filter(db_models.ReleaseFile.fhash=='lol3').one()

			f1_m_tags = set(f1.manga_tags)
			f1_h_tags = set(f1.hentai_tags)


			self.assertEqual(f1_m_tags, f2_m_tags | f3_m_tags)
			self.assertEqual(f1_h_tags, f2_h_tags | f3_h_tags)