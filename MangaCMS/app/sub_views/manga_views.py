
from flask import g
from flask import render_template
from flask import make_response
from flask import request

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

from .cache_control import CACHE_LIFETIME


def parse_table_args(**kwargs):

	print((request.args, kwargs))

	filter_params = {
		'distinct'        : [],
		'include-deleted' : [],
		'limit-by-source' : [],
		'filter-tags'      : [],
		'filter-category' : [],
	}

	print("Args:", request.args)
	print("kwargs:", kwargs)

	# Override the return parameters with the function
	# params (if passed).
	# Note: underscores are replaced with hyphens in the keys!
	for key, val in request.args.items(multi=True):
		print("args Key, val: ", key, val)
		key = key.replace("_", "-")
		if key in filter_params and val:
			filter_params[key].append(val)
	for key, val in kwargs.items():
		print("kwargs Key, val: ", key, val)
		key = key.replace("_", "-")
		if key in filter_params and val:
			filter_params[key].append(val)

	print("Filter params: ", filter_params)

	if 'distinct' in filter_params and filter_params['distinct'] and filter_params['distinct'][0].lower() == "true":
		filter_params['distinct'] = True
	if 'include-deleted' in filter_params and filter_params['include-deleted'] and filter_params['include-deleted'][0].lower() == "true":
		filter_params['include-deleted'] = True
	if 'limit-by-source' in filter_params and filter_params['limit-by-source']:
		for val in filter_params['limit-by-source']:
			if not val:
				continue
			val = val.lower()
			new = []
			if val in [tmp['key'] for tmp in all_scrapers_ever.all_scrapers]:
				new.append(val)
			else:
				print("Bad val: ", val, [tmp['key'] for tmp in all_scrapers_ever.all_scrapers])
			filter_params['limit-by-source'] = new

	if 'filter-tags' in filter_params and filter_params['filter-tags']:
		filter_params['filter-tags'] = [str(tmp) for tmp in filter_params['filter-tags']]
	if 'filter-category' in filter_params and filter_params['filter-category']:
		filter_params['filter-category'] = [str(tmp) for tmp in filter_params['filter-category']]

	return filter_params

def get_tags_for_tag_str(tag_table, tag_str):
	have_tags = g.session.query(tag_table).filter(tag_table.tag.like("%{}%".format(tag_str))).all()
	if have_tags:
		return have_tags
	else:
		return [-1]


def select_from_table(main_table, tag_table, link_table, page, site=False, filter_tags=None, filter_category=None):
	params = parse_table_args(limit_by_source=site, filter_tags=filter_tags, filter_category=filter_category)

	query = g.session.query(main_table) \
				.options(
						joinedload("file"),
						joinedload("file.hentai_tags_rel"),
						joinedload("tags_rel"),
						joinedload("file.hentai_releases"),
					)

	# query = query.join(tag_table)
	query = query.join(db.ReleaseFile)
	# query = query.filter( table = AC.id )


	if not params['include-deleted']:
		query = query.filter(main_table.deleted == False)
	if params['limit-by-source']:
		for source in params['limit-by-source']:
			query = query.filter(main_table.source_site == source)
	if params['filter-category']:
		for filter_cat in params['filter-category']:
			query = query.filter(main_table.series_name == filter_cat)

	print("params['filter-tags']", params['filter-tags'])

	if params['filter-tags']:
		all_filters = []

		# query.join(tag_table, link_table.c.releases_id == main_table.id)
		params['resolved-filter-tags'] = []
		for filter_tag in params['filter-tags']:
			filters = []
			tag_rows = get_tags_for_tag_str(tag_table, filter_tag)
			print("Adding filter:", tag_table, tag_table.tag, filter_tag, tag_table.tag == filter_tag, tag_rows)
			for tag_row in tag_rows:
				filt = main_table.id.in_(
						g.session.query(link_table.c.releases_id).filter(link_table.c.tags_id == tag_row.id)
					)
				filters.append(filt)
			params['resolved-filter-tags'].append([tmp.tag for tmp in tag_rows])
			all_filters.append(or_(*filters))
		query = query.filter(and_(*all_filters))

	if params['distinct']:
		query = query.distinct(main_table.series_name)             \
			.order_by(sql_desc(sql_max(main_table.downloaded_at)))
	else:
		query = query.order_by(main_table.downloaded_at.desc())

	# print("Query:")
	# print(query)
	print("Executing")
	ret = params, paginate(query, page=page)
	print("Query complete")
	return ret


@app.route('/manga/', methods=['GET'])
@app.route('/manga/page/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def manga_only_view(page=1):
	params, items = select_from_table(main_table=db.MangaReleases, tag_table=db.MangaTags, link_table=db.manga_files_tags_link, page=page)
	return render_template('manga_view.html',
						   whole_page    = True,
						   items         = items,
						   params        = params,
						   page          = page,
						   url_for_param = "manga_only_view"
						   )

@app.route('/manga/by-site/<source_site>/', methods=['GET'])
@app.route('/manga/by-site/<source_site>/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def manga_by_site_view(source_site, page=1):
	params, items = select_from_table(main_table=db.MangaReleases, tag_table=db.MangaTags, link_table=db.manga_files_tags_link, page=page, site=source_site)

	params['source_site'] = source_site
	print("Params: ", params)

	return render_template('manga_view.html',
						   whole_page    = True,
						   items         = items,
						   params        = params,
						   page          = page,
						   url_for_param = "manga_by_site_view"
						   )

@app.route('/hentai/', methods=['GET'])
@app.route('/hentai/page/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def hentai_only_view(page=1):
	params, items = select_from_table(main_table=db.HentaiReleases, tag_table=db.HentaiTags, link_table=db.hentai_releases_tags_link, page=page)
	print("Rendering")
	ret = render_template('hentai_view.html',
						   whole_page    = True,
						   items         = items,
						   params        = params,
						   page          = page,
						   url_for_param = "hentai_only_view"
						   )
	print("Rendered")
	return ret

@app.route('/hentai/by-site/<source_site>/', methods=['GET'])
@app.route('/hentai/by-site/<source_site>/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def hentai_by_site_view(source_site, page=1):
	params, items = select_from_table(main_table=db.HentaiReleases, tag_table=db.HentaiTags, link_table=db.hentai_releases_tags_link, page=page, site=source_site)
	return render_template('hentai_view.html',
						   whole_page    = True,
						   items         = items,
						   params        = params,
						   source_site   = source_site,
						   page          = page,
						   url_for_param = "hentai_by_site_view"
						   )

@app.route('/hentai/by-tag/<tag>/', methods=['GET'])
@app.route('/hentai/by-tag/<tag>/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def hentai_tag_view(tag, page=1):
	params, items = select_from_table(main_table=db.HentaiReleases, tag_table=db.HentaiTags, link_table=db.hentai_releases_tags_link, page=page, filter_tags=tag)
	return render_template('hentai_view.html',
						   whole_page    = True,
						   items         = items,
						   params        = params,
						   tag           = tag,
						   page          = page,
						   url_for_param = "hentai_tag_view"
						   )

@app.route('/hentai/by-category/<category>/', methods=['GET'])
@app.route('/hentai/by-category/<category>/<int:page>', methods=['GET'])
@cache.cached(timeout=CACHE_LIFETIME, query_string=True)
def hentai_category_view(category, page=1):
	params, items = select_from_table(main_table=db.HentaiReleases, tag_table=db.HentaiTags, link_table=db.hentai_releases_tags_link, page=page, filter_category=category)
	return render_template('hentai_view.html',
						   whole_page    = True,
						   items         = items,
						   params        = params,
						   category      = category,
						   page          = page,
						   url_for_param = "hentai_category_view"
						   )


