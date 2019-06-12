

import MangaCMS.db as db

def resetAllRunningFlags():
	'''
	clear the runstate for all the plugins in the status table. Helpful for when
	plugins crash without properly clearing their runstate.
	'''

	print("Resetting run state for all plugins via new interface!")
	with db.session_context() as sess:
		changed = sess.query(db.PluginStatus).update({"running" : False})
		print("Changed:", changed)

