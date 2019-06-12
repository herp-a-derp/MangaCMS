
import os
import os.path
from natsort import natsorted


from flask import g
from flask import render_template
from flask import make_response
from flask import redirect
from flask import url_for
from flask import request
from flask import flash

from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import max as sql_max
from sqlalchemy.sql.expression import desc as sql_desc

print("Manga View import!")
from MangaCMS.app import app
from MangaCMS.app import cache
from MangaCMS.app import all_scrapers_ever
from MangaCMS.app.utilities import paginate
import MangaCMS.db as db

import nameTools as nt

from .cache_control import CACHE_LIFETIME


def fSizeToStr(fSize):
	if fSize == 0:
		return ''

	fStr = fSize/1.0e6
	if fStr < 100:
		fStr = "%0.2f M" % fStr
	else:
		fStr = "%0.1f M" % fStr

	return fStr

def load_directory(dirPath):
	if not os.path.exists(dirPath):
		return []

	dirContents = os.listdir(dirPath)

	# If there are more then three "chapter 1" files, sort by volume, and then chapter, otherwise,
	# just sort by chapter.
	VOL_THRESHOLD = 3

	tmp = []
	for item in dirContents:
		chap, vol = nt.extractChapterVol(item)

		itemPath = os.path.join(dirPath, item)
		if not os.path.isdir(itemPath):
			sz = os.path.getsize(itemPath)
			szStr = fSizeToStr(sz)
		else:
			szStr = ''


		tmp.append((vol, chap, item, os.path.join(dirPath, item), szStr))

	chap1files = len([item for item in tmp if item[1] == 1])

	if not chap1files > VOL_THRESHOLD:
		dirContents = natsorted(tmp, key=lambda dat: (dat[1], dat))
	else:
		dirContents = natsorted(tmp)

	return dirContents




@app.route('/reader/by-series/<series_name>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def manga_by_series(series_name):
	print("Series Name:", series_name)
	print("nt.dirNameProxy:", nt.dirNameProxy.paths)

	itemDict = nt.dirNameProxy[series_name]

	print("ItemDict", itemDict)
	if not itemDict["item"]:
		flash('Series name %s not found!!' % (series_name, ))
		return redirect(url_for('manga_only_view'))


	sections = []

	for dirDictKey in nt.dirNameProxy.getDirDicts().keys():
		itemDictTemp = nt.dirNameProxy.getFromSpecificDict(dirDictKey, itemDict['dirKey'])
		if itemDictTemp and itemDictTemp["fqPath"]:
			dict_section = nt.dirNameProxy.getPathByKey(dirDictKey)
			sections.append((
				dict_section,
				itemDictTemp,
				load_directory(itemDictTemp['fqPath'])))


	# params, items = select_from_table(main_table=db.MangaReleases, tag_table=db.MangaTags, link_table=db.manga_files_tags_link, page=page, site=source_site)
	return render_template('manga_series_view.html',
						   series_meta      = itemDict,
						   sections         = sections,
						   # items         = items,
						   # params        = params,
						   )
