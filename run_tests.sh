#!/bin/bash

set -e

# alembic -n testing downgrade base
alembic -n testing upgrade head


python3 $(which nosetests)                       \
	--exe                                        \
	--stop                                       \
	--nocapture                                  \
	MangaCMS.test
	# Tests.Test_db_BKTree_Compare
	# Tests.Test_db_BKTree_Issue_2
	# Tests.Test_db_BKTree_Issue_1
	# Tests.Test_db_BKTree_2
	# Tests.Test_db_BKTree

coverage report --show-missing
coverage erase


# alembic -n testing downgrade base