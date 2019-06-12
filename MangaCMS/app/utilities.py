
# from app.models import Releases
# from sqlalchemy.sql.expression import nullslast
# from sqlalchemy import desc

from flask_sqlalchemy import Pagination
from flask import abort

from . import config




def paginate(query, page, per_page=100, error_out=True):
	if error_out and page < 1:
		abort(404)
	items = query.limit(per_page).offset((page - 1) * per_page).all()
	if not items and page != 1 and error_out:
		abort(404)

	# No need to count if we're on the first page and there are fewer
	# items than we expected.
	if page == 1 and len(items) < per_page:
		total = len(items)
	else:
		total = query.order_by(None).count()

	return Pagination(query, page, per_page, total, items)

