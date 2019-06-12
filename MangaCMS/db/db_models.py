
import datetime

from sqlalchemy.orm import backref
from sqlalchemy import Table
from sqlalchemy import Index

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import BigInteger
from sqlalchemy import Text
from sqlalchemy import Interval
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from sqlalchemy.ext.associationproxy import association_proxy

# Patch in knowledge of the citext type, so it reflects properly.
from sqlalchemy.dialects.postgresql.base import ischema_names

import sqlalchemy_jsonfield
import citext
ischema_names['citext'] = citext.CIText


from .db_engine import _session_factory
from .db_base import Base
from .db_types import file_type
from .db_types import dir_type
from .db_types import dlstate_enum


########################################################################################

manga_files_tags_link = Table(
		'manga_files_tags_link', Base.metadata,
		Column('releases_id', Integer, ForeignKey('release_files.id'), nullable=False),
		Column('tags_id',     Integer, ForeignKey('manga_tags.id'),  nullable=False),
		PrimaryKeyConstraint('releases_id', 'tags_id')
	)
manga_releases_tags_link = Table(
		'manga_releases_tags_link', Base.metadata,
		Column('releases_id', Integer, ForeignKey('manga_releases.id'), nullable=False),
		Column('tags_id',     Integer, ForeignKey('manga_tags.id'),  nullable=False),
		PrimaryKeyConstraint('releases_id', 'tags_id')
	)

class MangaTags(Base):
	__tablename__ = 'manga_tags'
	id          = Column(Integer, primary_key=True)
	tag         = Column(citext.CIText(), nullable=False, index=True)

	__table_args__ = (
			UniqueConstraint('tag'),
			CheckConstraint('length(tag) >= 2'),
		)

	@classmethod
	def get_or_create(cls, tag):
		tmp = _session_factory.query(cls)    \
			.filter(cls.tag == tag) \
			.scalar()
		if tmp:
			_session_factory.expunge(tmp)
			return tmp

		# print("manga_tag_creator", tag)
		tmp = cls(tag=tag)
		_session_factory.add(tmp)
		_session_factory.commit()
		_session_factory.expunge(tmp)
		return tmp

########################################################################################

hentai_files_tags_link = Table(
		'hentai_files_tags_link', Base.metadata,
		Column('releases_id', Integer, ForeignKey('release_files.id'), nullable=False, index=True),
		Column('tags_id',     Integer, ForeignKey('hentai_tags.id'),  nullable=False, index=True),
		PrimaryKeyConstraint('releases_id', 'tags_id')
	)
hentai_releases_tags_link = Table(
		'hentai_releases_tags_link', Base.metadata,
		Column('releases_id', Integer, ForeignKey('hentai_releases.id'), nullable=False, index=True),
		Column('tags_id',     Integer, ForeignKey('hentai_tags.id'),  nullable=False, index=True),
		PrimaryKeyConstraint('releases_id', 'tags_id')
	)

class HentaiTags(Base):
	__tablename__ = 'hentai_tags'
	id          = Column(Integer, primary_key=True)
	tag         = Column(citext.CIText(), nullable=False, index=True)

	__table_args__ = (
			UniqueConstraint('tag'),
			CheckConstraint('length(tag) >= 2'),
		)

	@classmethod
	def get_or_create(cls, tag):
		tmp = _session_factory.query(cls)    \
			.filter(cls.tag == tag) \
			.scalar()
		if tmp:
			_session_factory.expunge(tmp)
			return tmp

		# print("hentai_tag_creator", tag)
		tmp = cls(tag=tag)
		_session_factory.add(tmp)
		_session_factory.commit()
		_session_factory.expunge(tmp)
		return tmp


########################################################################################

class MangaReleases(Base):
	__tablename__ = 'manga_releases'
	id                  = Column(BigInteger, primary_key=True)
	state               = Column(dlstate_enum, nullable=False, index=True, default='new')
	err_str             = Column(Text)

	source_site         = Column(Text, nullable=False, index=True)  # Actual source site
	source_id           = Column(Text, nullable=False, index=True)  # ID On source site. Usually (but not always) the item URL

	first_seen          = Column(DateTime, nullable=False)
	posted_at           = Column(DateTime, nullable=False, default=datetime.datetime.min)
	downloaded_at       = Column(DateTime, nullable=False, default=datetime.datetime.min)
	last_checked        = Column(DateTime, nullable=False, default=datetime.datetime.min)

	deleted             = Column(Boolean, default=False, nullable=False)
	was_duplicate       = Column(Boolean, default=False, nullable=False)
	phash_duplicate     = Column(Boolean, default=False, nullable=False)
	uploaded            = Column(Boolean, default=False, nullable=False)

	dirstate            = Column(dir_type, nullable=False, default="unknown")

	origin_name         = Column(citext.CIText())
	series_name         = Column(citext.CIText(), index=True)

	additional_metadata = Column(sqlalchemy_jsonfield.JSONField())

	fileid              = Column(BigInteger, ForeignKey('release_files.id'))
	file                = relationship('ReleaseFile', backref='manga_releases')

	tags_rel       = relationship('MangaTags',
										secondary        = manga_releases_tags_link,
										backref          = backref("manga_releases", lazy='dynamic'),
										collection_class = set)
	tags           = association_proxy('tags_rel', 'tag', creator=MangaTags.get_or_create)

	__table_args__ = (
			UniqueConstraint('source_site', 'source_id'),
			Index('manga_releases_source_site_id_idx', 'source_site', 'source_id')
		)



class HentaiReleases(Base):
	__tablename__ = 'hentai_releases'
	id                  = Column(BigInteger, primary_key=True)
	state               = Column(dlstate_enum, nullable=False, index=True, default='new')
	err_str             = Column(Text)

	source_site         = Column(Text, nullable=False, index=True)  # Actual source site
	source_id           = Column(Text, nullable=False, index=True)  # ID On source site. Usually (but not always) the item URL

	first_seen          = Column(DateTime, nullable=False)
	posted_at           = Column(DateTime, nullable=False, default=datetime.datetime.min)
	downloaded_at       = Column(DateTime, nullable=False, default=datetime.datetime.min)
	last_checked        = Column(DateTime, nullable=False, default=datetime.datetime.min)

	deleted             = Column(Boolean, default=False, nullable=False)
	was_duplicate       = Column(Boolean, default=False, nullable=False)
	phash_duplicate     = Column(Boolean, default=False, nullable=False)
	uploaded            = Column(Boolean, default=False, nullable=False)

	dirstate            = Column(dir_type, nullable=False, default="unknown")

	origin_name         = Column(citext.CIText())
	series_name         = Column(citext.CIText(), index=True)

	additional_metadata = Column(sqlalchemy_jsonfield.JSONField())

	fileid              = Column(BigInteger, ForeignKey('release_files.id'))
	file                = relationship('ReleaseFile', backref='hentai_releases')

	tags_rel       = relationship('HentaiTags',
										secondary=hentai_releases_tags_link,
										backref=backref("hentai_releases", lazy='dynamic'),
										collection_class=set)
	tags           = association_proxy('tags_rel', 'tag', creator=HentaiTags.get_or_create)

	__table_args__ = (
			UniqueConstraint('source_site', 'source_id'),
			Index('hentai_releases_source_site_id_idx', 'source_site', 'source_id')
		)


class BookReleases(Base):
	__tablename__ = 'book_releases'
	id                  = Column(BigInteger, primary_key=True)
	state               = Column(dlstate_enum, nullable=False, index=True, default='new')
	err_str             = Column(Text)

	source_site         = Column(Text, nullable=False, index=True)  # Actual source site
	source_id           = Column(Text, nullable=False, index=True)  # ID On source site. Usually (but not always) the item URL

	first_seen          = Column(DateTime, nullable=False)
	posted_at           = Column(DateTime, nullable=False, default=datetime.datetime.min)
	downloaded_at       = Column(DateTime, nullable=False, default=datetime.datetime.min)
	last_checked        = Column(DateTime, nullable=False, default=datetime.datetime.min)

	deleted             = Column(Boolean, default=False, nullable=False)
	was_duplicate       = Column(Boolean, default=False, nullable=False)
	phash_duplicate     = Column(Boolean, default=False, nullable=False)
	uploaded            = Column(Boolean, default=False, nullable=False)

	dirstate            = Column(dir_type, nullable=False, default="unknown")

	origin_name         = Column(citext.CIText())
	series_name         = Column(citext.CIText(), index=True)

	additional_metadata = Column(sqlalchemy_jsonfield.JSONField())

	fileid              = Column(BigInteger, ForeignKey('release_files.id'))
	file                = relationship('ReleaseFile', backref='book_releases')

	__table_args__ = (
			UniqueConstraint('source_site', 'source_id'),
			Index('book_releases_source_site_id_idx', 'source_site', 'source_id')
		)



class ReleaseFile(Base):
	__tablename__ = 'release_files'
	id             = Column(BigInteger, primary_key=True)

	dirpath        = Column(Text, nullable=False)
	filename       = Column(Text, nullable=False, index=True)
	fhash          = Column(Text, nullable=False, index=True)
	file_type      = Column(file_type, nullable=False, default="unknown")

	was_duplicate       = Column(Boolean, default=False, nullable=False)

	last_dup_check = Column(DateTime, nullable=False, default=datetime.datetime.min)

	manga_tags_rel       = relationship('MangaTags',
										secondary=manga_files_tags_link,
										backref=backref("release_files", lazy='dynamic'),
										collection_class=set)
	manga_tags           = association_proxy('manga_tags_rel', 'tag', creator=MangaTags.get_or_create)

	hentai_tags_rel      = relationship('HentaiTags',
										secondary=hentai_files_tags_link,
										backref=backref("release_files", lazy='dynamic'),
										collection_class=set)
	hentai_tags          = association_proxy('hentai_tags_rel', 'tag', creator=HentaiTags.get_or_create)

	# releases       = relationship('MangaReleases')

	__table_args__ = (
			UniqueConstraint('dirpath', 'filename'),
			UniqueConstraint('fhash'),
		)



class PluginStatus(Base):
	__tablename__ = 'plugin_status'
	id             = Column(Integer, primary_key=True)

	name           = Column(Text, nullable=False, unique=True, index=True)
	last_output    = Column(Text)
	running        = Column(Boolean, nullable=False, default=False)

	last_run       = Column(DateTime, nullable=False, default=datetime.datetime.min)
	last_error     = Column(DateTime, nullable=False, default=datetime.datetime.min)
	run_time       = Column(Interval, nullable=False, default=datetime.timedelta)


