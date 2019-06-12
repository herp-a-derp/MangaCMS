
import sys
import logging
import contextlib
import traceback


from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

import time


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy

import queue

from settings import MAX_DB_SESSIONS
from settings import NEW_DATABASE_IP            as C_DATABASE_IP
from settings import NEW_DATABASE_DB_NAME       as C_DATABASE_DB_NAME
from settings import NEW_DATABASE_USER          as C_DATABASE_USER
from settings import NEW_DATABASE_PASS          as C_DATABASE_PASS


if '__pypy__' in sys.builtin_module_names:
	SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2cffi://{user}:{passwd}@{host}:5432/{database}'.format(user=C_DATABASE_USER, passwd=C_DATABASE_PASS, host=C_DATABASE_IP, database=C_DATABASE_DB_NAME)
else:
	SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{passwd}@{host}:5432/{database}'.format(user=C_DATABASE_USER, passwd=C_DATABASE_PASS, host=C_DATABASE_IP, database=C_DATABASE_DB_NAME)


# I was having issues with timeouts because the default connection pool is 5 connections.
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size = MAX_DB_SESSIONS, isolation_level='REPEATABLE_READ')

SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
_session_factory = scoped_session(SessionFactory)

context_logger = logging.getLogger("Main.SessionContext")

def new_session():
	return _session_factory()

def delete_db_session(sess):
	sess.close()
	_session_factory.remove()


@contextlib.contextmanager
def session_context(commit=True, reuse_sess=None):

	# Allow the optional reuse of a existing session, which makes
	# control flow a LOT easier in some cases.
	if reuse_sess:
		yield reuse_sess
		return

	else:

		sess = _session_factory()

		try:
			yield sess

		except Exception as e:
			context_logger.error("Error in transaction!")
			for line in traceback.format_exc().split("\n"):
				context_logger.error(line)
			context_logger.warning("Rolling back.")
			sess.rollback()
			sess.close()
			_session_factory.remove()
			raise e

		finally:
			if commit:
				sess.commit()
			sess.close()
			_session_factory.remove()

