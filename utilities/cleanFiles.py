# import sys
# sys.path.insert(0,"..")
import os.path
import os
import MangaCMSOld.lib.logSetup
if __name__ == "__main__":
	MangaCMSOld.lib.logSetup.initLogging()

import UniversalArchiveInterface
import traceback

import runStatus
runStatus.preloadDicts = False

import MangaCMSOld.cleaner.archCleaner

def cleanArchives(baseDir):
	print(baseDir)
	cleaner = MangaCMSOld.cleaner.archCleaner.ArchCleaner()

	for root, dirs, files in os.walk(baseDir):
		for name in files:
			fileP = os.path.join(root, name)
			print("Processing", fileP)

			try:
				if UniversalArchiveInterface.ArchiveReader.isArchive(fileP):
					cleaner.cleanZip(fileP)

			except KeyboardInterrupt:
				raise

			except:
				print("ERROR")
				traceback.print_exc()
				pass