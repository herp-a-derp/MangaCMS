
import os.path
import mimetypes
import pickle
import time
import datetime
import urllib.parse
from calendar import timegm

from flask import g
from flask import render_template
from flask import make_response
from flask import request
from flask import flash
from flask import redirect
from flask import url_for

from sqlalchemy.sql import text


from MangaCMS.app import app
import MangaCMS.db as db
import nameTools


from . import reader_session_manager

def guessItemMimeType(itemName):
	mime_type = mimetypes.guess_type(itemName)
	print("Inferred MIME type %s for file %s" % (mime_type,  itemName))
	if mime_type:
		return mime_type[0]
	return "application/unknown"


def fix_sort_djm(keys):
	if not keys:
		return []

	id1, name1 = keys[0]
	try:
		maybe_num = int(name1.split(" ")[0].split(".")[0])
		return [key[0] for key in keys]
	except ValueError:
		# Item has the old numbering, we have to use the second entry
		# to do the sorting
		pass

	keys.sort(key=lambda x: x[1].split(" ")[-1].split(".")[0])

	return [key[0] for key in keys]


@app.route('/reader/h/<int:rid>', methods=['GET'])
def view_h_by_id(rid):
	session = g.session

	series_row = session.query(db.HentaiReleases) \
		.filter(db.HentaiReleases.id == rid)  \
		.scalar()

	source = series_row.source_site

	if not series_row:
		flash('Series id %s not found!' % rid)
		return redirect(url_for('hentai_only_view'))

	if not series_row.file:
		flash('Series id %s has no file!' % rid)
		return redirect(url_for('hentai_only_view'))

	item_path = os.path.join(series_row.file.dirpath, series_row.file.filename)

	if not (os.path.isfile(item_path) and os.access(item_path, os.R_OK)):

		flash('Series id %s file path doesn\'t exist (%s)!' % (rid, item_path))
		return redirect(url_for('hentai_only_view'))

	try:
		# We have a valid file-path. Read it!
		session_manager = reader_session_manager.SessionPoolManager()
		session_manager[("h", rid)].checkOpenArchive(item_path)
		keys = session_manager[("h", rid)].getKeys()  # Keys are already sorted

	except Exception:
		flash('Error opening series file for id %s (%s)!' % (rid, item_path))
		return redirect(url_for('hentai_only_view'))

	if source == 'djm':
		keys = fix_sort_djm(session_manager[("h", rid)].getKeyNameMapping())


	filename = series_row.file.filename
	image_urls = [
		"/reader/h/{hid}/{hpg}".format(hid=rid, hpg=key) for key in keys
		]

	ret = render_template('reader/readBase.html',
						   image_urls  = image_urls,
						   filename    = filename,
						   )

	session.commit()

	return ret


@app.route('/reader/by-path/', methods=['GET'])
def manga_by_path():

	item_path = request.args.get('path', None)
	pagen = request.args.get('page', None)

	if not item_path:
		flash('No path?')
		return redirect(url_for('manga_only_view'))

	file_valid = nameTools.dirNameProxy.is_subdir_of_paths(item_path)
	if not file_valid:
		flash('Path %s not valid!' % item_path)
		return redirect(url_for('manga_only_view'))

	if not pagen:
		# We have
		if not (os.path.isfile(item_path) and os.access(item_path, os.R_OK)):

			flash('File path doesn\'t exist (%s)!' % (item_path, ))
			return redirect(url_for('manga_only_view'))

		try:
			# We have a valid file-path. Read it!
			session_manager = reader_session_manager.SessionPoolManager()
			session_manager[("m", item_path)].checkOpenArchive(item_path)
			keys = session_manager[("m", item_path)].getKeys()  # Keys are already sorted

		except Exception:
			flash('Error opening file "%s"!' % (item_path, ))
			return redirect(url_for('manga_only_view'))


		filename = os.path.split(item_path)[-1]
		image_urls = []
		for key in keys:
			print("Key: '%s'" % (key, ))
			query_string = urllib.parse.urlencode(
					{
						"path" : str(item_path),
						"page" : str(key),
					}
				)
			url =  "/reader/by-path/?{query_string}".format(query_string = query_string)

		image_urls = [
			"/reader/by-path/?{query_string}".format(query_string = urllib.parse.urlencode({
				"path" : item_path,
				"page" : key,
				})) for key in keys
			]

		ret = render_template('reader/readBase.html',
							   image_urls  = image_urls,
							   filename    = filename,
							   )

		return ret

	if pagen is not None:
		pagen = int(pagen)
		sess_key = ("m", item_path)

		session_manager = reader_session_manager.SessionPoolManager()
		if not sess_key in session_manager:
			flash('No open session for manga path %s!' % (item_path, ))
			return redirect(url_for('manga_only_view'))

		itemFileHandle, itemPath = session_manager[sess_key].getItemByKey(pagen)

		response = make_response(itemFileHandle.read())
		response.headers['Content-Type']        = guessItemMimeType(itemPath)
		response.headers['Content-Disposition'] = "inline; filename=" + itemPath.split("/")[-1]
		return response


	flash('Uh, what?')
	return redirect(url_for('manga_only_view'))



@app.route('/reader/h/<int:rid>/<int:page>', methods=['GET'])
def view_h_by_id_page(rid, page):

	session_manager = reader_session_manager.SessionPoolManager()
	if not ("h", rid) in session_manager:
		flash('No open session for hentai id %s!' % (rid, ))
		return redirect(url_for('hentai_only_view'))

	itemFileHandle, itemPath = session_manager[("h", rid)].getItemByKey(page)

	response = make_response(itemFileHandle.read())
	response.headers['Content-Type']        = guessItemMimeType(itemPath)
	response.headers['Content-Disposition'] = "inline; filename=" + itemPath.split("/")[-1]
	return response



@app.route('/reader/m/<int:rid>', methods=['GET'])
def view_m_by_id(rid):
	session = g.session

	series_row = session.query(db.HentaiReleases) \
		.filter(db.HentaiReleases.id == rid)  \
		.scalar()


	if not series_row:
		flash('Series id %s not found!' % rid)
		return redirect(url_for('manga_only_view'))

	if not series_row.file:
		flash('Series id %s has no file!' % rid)
		return redirect(url_for('manga_only_view'))

	item_path = os.path.join(series_row.file.dirpath, series_row.file.filename)

	if not (os.path.isfile(item_path) and os.access(item_path, os.R_OK)):

		flash('Series id %s file path doesn\'t exist (%s)!' % (rid, item_path))
		return redirect(url_for('manga_only_view'))

	try:
		# We have a valid file-path. Read it!
		session_manager = reader_session_manager.SessionPoolManager()
		session_manager[("m", rid)].checkOpenArchive(item_path)
		keys = session_manager[("m", rid)].getKeys()  # Keys are already sorted

	except Exception:
		flash('Error opening series file for id %s (%s)!' % (rid, item_path))
		return redirect(url_for('manga_only_view'))

	filename = series_row.file.filename
	image_urls = [
		"/reader/m/{hid}/{hpg}".format(hid=rid, hpg=key) for key in keys
		]

	ret = render_template('reader/readBase.html',
						   image_urls  = image_urls,
						   filename    = filename,
						   )

	session.commit()

	return ret



@app.route('/reader/m/<int:rid>/<int:page>', methods=['GET'])
def view_m_by_id_page(rid, page):

	session_manager = reader_session_manager.SessionPoolManager()
	if not ("m", rid) in session_manager:
		flash('No open session for manga id %s!' % (rid, ))
		return redirect(url_for('manga_only_view'))

	itemFileHandle, itemPath = session_manager[("m", rid)].getItemByKey(page)

	response = make_response(itemFileHandle.read())
	response.headers['Content-Type']        = guessItemMimeType(itemPath)
	response.headers['Content-Disposition'] = "inline; filename=" + itemPath.split("/")[-1]
	return response
