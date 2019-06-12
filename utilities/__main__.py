

print("Utilities Startup")
import runStatus
runStatus.preloadDicts = False

import MangaCMSOld.lib.logSetup
MangaCMSOld.lib.logSetup.initLogging()

import signal
import sys
import os.path
import utilities.dedupDir
import MangaCMS.util.runPlugin
import utilities.approxFileSorter
import utilities.autoOrganize as autOrg
import utilities.importer as autoImporter
import utilities.cleanDb
import utilities.bookClean
import utilities.cleanFiles
import deduplicator.remoteInterface
import MangaCMS.lib.statusManager

help_strings = [
	"################################### ",
	"##   System maintenance script   ## ",
	"################################### ",
	"",
	"*********************************************************",
	"Runtime Tools",
	"*********************************************************",
	"	run {plug_key}",
	"		Execute plugin {plug_key}.",
	"		If plugin is not specified, print the available plugins",
	"		The special meta-plugin value of 'all' will run all plugins",
	"		in sequence",
	"",
	"	retag {plug_key}",
	"		Retag items for {plug_key}.",
	"		If plugin is not specified, print the available plugins",
	"",
	"",
	"*********************************************************",
	"Organizing Tools",
	"*********************************************************",
	"	import {dirPath}",
	"		Import folders of manga from {dirPath}",
	"		Assumes that {dirPath} is composed of directories containing manga",
	"		zip files, and the directory is named after the series that it contains.",
	"",
	"	organize {dirPath}",
	"		Run auto_organizing tools against {dirPath}",
	"",
	"	rename {dirPath}",
	"		Rename directories in {dirPath} to match MangaUpdates naming",
	"",
	"	dirs_clean {target_path} {del_dir}",
	"		Find duplicates in each subdir of {target_path}, and remove them.",
	"		Functions on a per_directory basis, so only duplicates in the same folder will be considered",
	"		Does not currently use phashing.",
	"		'Deleted' files are actually moved to {del_dir}, to allow checking before actual deletion.",
	"		The moved files are named with the entire file_path, with the '/' being replaced with ';'.",
	"",
	"	dir_clean {target_path} {del_dir}",
	"		Find duplicates in {target_path}, and remove them.",
	"		Functions on a per_directory basis, so only duplicates in the same folder will be considered",
	"		Does not currently use phashing.",
	"		'Deleted' files are actually moved to {del_dir}, to allow checking before actual deletion.",
	"		The moved files are named with the entire file_path, with the '/' being replaced with ';'.",
	"	",
	"	dirs_restore {target_path}",
	"		Reverses the action of 'dirs_clean'. {target_path} is the directory specified as ",
	"		{del_dir} when running 'dirs_clean' ",
	"	",
	"	purge_dir {target_path}",
	"		Processes the output of 'dirs_clean'. {target_path} is the directory specified as ",
	"		{del_dir} when running 'dirs_clean'. ",
	"		Each item in {del_dir} is re_confirmed to be a complete duplicate, and then truly deleted. ",
	"	",
	"	purge_dir_phash {target_path}",
	"		Same as `purge_dir`, but uses phashes for duplicate detection as well.",
	"	",
	"	sort_dir_contents {target_path}",
	"		Scan the contents of {target_path}, and try to infer the series for each file in said folders.",
	"		If file doesn't match the series for the folder, and does match a known, valid folder, prompt",
	"		to move to valid folder.",
	"	",
	"	move_unlinked {src_path} {to_path}",
	"		Scan the contents of {src_path}, and try to infer the series for each subdirectory.",
	"		If a subdir has no matching series, move it to {to_path}",
	"	",
	"	h_clean",
	"		Walk through the historical H items and remove superceded duplicates.",
	"		Processing is done in DB_ID order, which is roughtly chronological..",
	"	",
	"	k_clean",
	"		Functions identically to the h_cleaner, but operates on the kissmange database entries",
	"	",
	"	clean_reset",
	"		Remove the incremental scan progress tags from the manga and hentai database.",
	"	",
	"	m_clean",
	"		And for cleaning all manga items.",
	"	",
	"	src_clean {source_key} {del_dir}",
	"		Find duplicates for all the items downloaded under the key {source_key}, and remove them.",
	"		'Deleted' files are actually moved to {del_dir}, to allow checking before actual deletion.",
	"		The moved files are named with the entire file_path, with the '/' being replaced with ';'.",
	"	fix_swapped_paths",
	"		Fix items where the path and filename are swapped in the database.",
	"	",
	"	",
	"*********************************************************",
	"Miscellaneous Tools",
	"*********************************************************",
	"	lookup {name}",
	"		Lookup {name} in the MangaUpdates name synonym lookup table, print the results.",
	"",
	"	crosslink_books",
	"		Make sure the netloc column of the book_items table is up to date.",
	"",
	"	clean_book_cache",
	"		Clean out and delete any old files from the book content cache",
	"		that no longer has any entries in the database.",
	"",
	"	rescan_failed_h",
	"		Rescan all H items that failed on previous phash processing.",
	"",
	"",
	"*********************************************************",
	"Database Maintenance",
	"*********************************************************",
	"	reset_missing",
	"		Reset downloads where the file is missing, and the download is not tagged as deduplicated.",
	"	",
	"	clear_bad_dedup",
	"		Remove deduplicated tag from any files where the file exists.",
	"	",
	"	fix_bt_links",
	"		Fix links for Batoto that point to batoto.com, rather then bato.to.",
	"	",
	"	cross_sync",
	"		Sync name lookup table with seen series.",
	"	",
	"	update_bu_lut",
	"		Regernate lookup strings for MangaUpdates table (needed if the `prepFilenameForMatching` call in nameTools is modified).",
	"	",
	"	fix_bad_series",
	"		Consolidate series names to MangaUpdates standard naming.",
	"	",
	"	reload_tree",
	"		Reload the BK tree from the database.",
	"	",
	"	lndb_cleaned_regen",
	"		regenerate the set of cleaned LNDB item titles..",
	"	",
	"	fix_book_link_sources",
	"		",
	"	",
	"	fix_bu_authors",
	"		Fix authors from mangaupdates table where '[, Add, ]' got into the data due to incomplete parsing of the webpage",
	"	",
	"	clean_h_tags",
	"		Fix issues where mixed_case H tags were being duplicated.",
	"	",
	"	clean_japanese_only",
	"		Clear out item in the H database that is not translated and has no tags we care about.",
	"	",
	"	clean_yaoi_only",
	"		Clear out item in the H database that is yaoi and has no tags we care about.",
	"	",
	"	aggregate_crosslinks",
	"		Aggregate cross_linked entries in the H database.",
	"	",
	"	",
	"	reprocess_from_db_bak {path}",
	"		Given a tar.gz database backup, extract and update hentai tags from it.",
	"	",
	"	",
	"*********************************************************",
	"Remote deduper interface",
	"*********************************************************",
	"	phash_clean {targetDir} {removeDir}",
	"		Find duplcates on the path {targetDir}, and move them to {removeDir}",
	"		Duplicate search is done using the set of phashes contained within ",
	"		{scanEnv}. ",
	"		Requires deduper server interface to be running.",
]



##############################################################################################################################
# Function Stubs
##############################################################################################################################

# Single arg (funcs take no arg):
def reset_b_missing():
	pc = utilities.cleanDb.BCleaner()
	pc.resetMissingDownloads()
def reset_m_missing():
	pc = utilities.cleanDb.MCleaner()
	pc.resetMissingDownloads()
def reset_h_missing():
	pc = utilities.cleanDb.HCleaner()
	pc.resetMissingDownloads()
def clear_bad_dedup():
	pc = utilities.cleanDb.PathCleaner()
	pc.clearInvalidDedupTags()
def clear_bad_h_dedup():
	hc = utilities.cleanDb.HCleaner()
	hc.clearInvalidDedupTags()
def fix_batoto_urls():
	pc = utilities.cleanDb.PathCleaner()
	pc.btUrlFix()
def fix_bt_links():
	pc = utilities.cleanDb.PathCleaner()
	pc.patchBatotoLinks()
def cross_sync():
	pc = utilities.cleanDb.PathCleaner()
	pc.crossSyncNames()
def update_bu_lut():
	pc = utilities.cleanDb.PathCleaner()
	pc.regenerateNameMappings()
def fix_bad_series():
	pc = utilities.cleanDb.PathCleaner()
	pc.consolidateSeriesNaming()
def fix_djm():
	pc = utilities.cleanDb.PathCleaner()
	pc.fixDjMItems()
def clean_h_tags():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.cleanTags()
def clean_japanese_only():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.cleanJapaneseOnly()
def clean_cg_only():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.cleanCgOnly()
def clean_yaoi_only():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.cleanYaoiOnly()
def sync_h_file_tags():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.syncHFileTags()
def refetch_missing_tags():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.refetch_missing_tags()
def aggregate_crosslinks():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.aggregateCrossLinks()
def fix_single_letter_tags():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.fixSingleLetterTags()
def reprocess_damaged():
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.reprocess_damanged()

def fix_present_files():
	hcleaner = utilities.cleanDb.HCleaner('None')
	hcleaner.fixDlstateForPresentFiles()
	mcleaner = utilities.cleanDb.MCleaner('None')
	mcleaner.fixDlstateForPresentFiles()

def delete_null_rows():
	hcleaner = utilities.cleanDb.HCleaner('None')
	hcleaner.deleteNullRows()
	mcleaner = utilities.cleanDb.MCleaner('None')
	mcleaner.deleteNullRows()


def validate_hashes():
	mcleaner = utilities.cleanDb.MCleaner('None')
	mcleaner.check_file_hashes()

def reset_run_states():
	MangaCMS.lib.statusManager.resetAllRunningFlags()


# Double arg (funcs take one parameter):
def two_arg_import(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	autoImporter.importDirectories(val)

def two_arg_organize(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	autOrg.organizeFolder(val)

def two_arg_fix_escapes(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	autOrg.fix_escapes(val)

def two_arg_run(val):
	MangaCMS.util.runPlugin.runPlugin(val)

def two_arg_rename(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	autOrg.renameSeriesToMatchMangaUpdates(val)

def two_arg_lookup(val):
	print("Passed name = '%s'" % val)
	import nameTools as nt
	haveLookup = nt.haveCanonicalMangaUpdatesName(val)
	if not haveLookup:
		print("Item not found in MangaUpdates name synonym table")
		print("Processed item as searched = '%s'" % nt.prepFilenameForMatching(val))
	else:
		print("Item found in lookup table!")
		print("Canonical name = '%s'" % nt.getCanonicalMangaUpdatesName(val) )

def two_arg_purge_dir(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	utilities.dedupDir.purgeDedupTemps(val)
def two_arg_purge_dir_phash(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	utilities.dedupDir.purgeDedupTempsPhash(val)

def two_arg_dirs_restore(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	utilities.dedupDir.runRestoreDeduper(val)

def two_arg_sort_dir_contents(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	utilities.approxFileSorter.scanDirectories(val)

def two_arg_reprocess_from_db_bak(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	cleaner = utilities.cleanDb.HCleaner('None')
	cleaner.reprocess_from_db_bak(val)


def two_arg_clean_archives(val):
	if not os.path.exists(val):
		print("Passed path '%s' does not exist!" % val)
		return
	utilities.cleanFiles.cleanArchives(val)

# Triple arg (funcs take two parameters):


def three_arg_dirs_clean(arg1, arg2):
	if not os.path.exists(arg1):
		print("Passed path '%s' does not exist!" % arg1)
		return
	elif not os.path.exists(arg2):
		print("Passed path '%s' does not exist!" % arg2)
		return
	utilities.dedupDir.runDeduper(arg1, arg2)

def three_arg_src_clean(arg1, arg2):
	if not os.path.exists(arg2):
		print("Passed path '%s' does not exist!" % arg2)
		return
	utilities.dedupDir.runSrcDeduper(arg1, arg2)

def three_arg_dir_clean(arg1, arg2):
	if not os.path.exists(arg1):
		print("Passed path '%s' does not exist!" % arg1)
		return
	if not os.path.exists(arg2):
		print("Passed path '%s' does not exist!" % arg2)
		return
	utilities.dedupDir.runSingleDirDeduper(arg1, arg2)

def three_arg_move_unlinked(arg1, arg2):
	if not os.path.exists(arg1):
		print("Passed path '%s' does not exist!" % arg1)
		return
	if not os.path.exists(arg2):
		print("Passed path '%s' does not exist!" % arg2)
		return
	utilities.dedupDir.moveUnlinkable(arg1, arg2)

def three_arg_auto_clean(arg1, arg2):
	if not os.path.exists(arg1):
		print("Passed path '%s' does not exist!" % arg1)
		return
	if not os.path.exists(arg2):
		print("Passed path '%s' does not exist!" % arg2)
		return
	deduplicator.remoteInterface.iterateClean(arg1, arg2)

# def three_arg_h_fix(arg1, arg2):
# 	if not os.path.exists(arg2):
# 		print("Passed path '%s' does not exist!" % arg2)
# 		return

# 	cleaner = utilities.cleanDb.HCleaner(arg1)
# 	cleaner.resetMissingDownloads(arg2)

def three_arg_phash_clean(arg1, arg2):
	if not os.path.exists(arg1):
		print("Passed path '%s' does not exist!" % arg1)
		return
	if not os.path.exists(arg2):
		print("Passed path '%s' does not exist!" % arg2)
		return
	deduplicator.remoteInterface.pClean(arg1, arg2)




##############################################################################################################################
##############################################################################################################################

single_arg_funcs = {

	"run"                     : MangaCMS.util.runPlugin.listPlugins,
	'retag'                   : MangaCMS.util.runPlugin.listPlugins,
	"reload_tree"             : deduplicator.remoteInterface.treeReload,
	"crosslink_books"         : utilities.bookClean.updateNetloc,
	"clean_book_cache"        : utilities.bookClean.cleanBookContent,
	"lndb_cleaned_regen"      : utilities.bookClean.regenLndbCleanedNames,
	"fix_book_link_sources"   : utilities.bookClean.fixBookLinkSources,
	"fix_bu_authors"          : utilities.bookClean.fixMangaUpdatesAuthors,

	"reset_b_missing"         : reset_b_missing,
	"reset_m_missing"         : reset_m_missing,
	"reset_h_missing"         : reset_h_missing,
	"clear_bad_dedup"         : clear_bad_dedup,
	"clear_bad_h_dedup"       : clear_bad_h_dedup,
	"validate_hashes"         : validate_hashes,

	"fix_batoto_urls"         : fix_batoto_urls,
	"fix_bt_links"            : fix_bt_links,
	"cross_sync"              : cross_sync,
	"update_bu_lut"           : update_bu_lut,
	"fix_bad_series"          : fix_bad_series,
	"fix_djm"                 : fix_djm,
	"clean_h_tags"            : clean_h_tags,
	"clean_cg_only"           : clean_cg_only,
	"clean_japanese_only"     : clean_japanese_only,
	"clean_yaoi_only"         : clean_yaoi_only,
	"aggregate_crosslinks"    : aggregate_crosslinks,
	"fix_single_letter_tags"  : fix_single_letter_tags,
	"reprocess_damaged"       : reprocess_damaged,
	"fix_present_files"       : fix_present_files,
	"delete_null_rows"        : delete_null_rows,
	"sync_h_file_tags"        : sync_h_file_tags,
	"refetch_missing_tags"    : refetch_missing_tags,
	"reset_run_states"        : reset_run_states,

}

double_arg_funcs = {
	"clean_archives"          : two_arg_clean_archives,
	"dirs_restore"            : two_arg_dirs_restore,
	"import"                  : two_arg_import,
	"lookup"                  : two_arg_lookup,
	"organize"                : two_arg_organize,
	"fix_escapes"             : two_arg_fix_escapes,
	"purge_dir"               : two_arg_purge_dir,
	"purge_dir_phash"         : two_arg_purge_dir_phash,
	"rename"                  : two_arg_rename,
	"reprocess_from_db_bak"   : two_arg_reprocess_from_db_bak,
	"run"                     : two_arg_run,
	"sort_dir_contents"       : two_arg_sort_dir_contents,

}

triple_arg_funcs = {
	"dirs_clean"    : three_arg_dirs_clean,
	"src_clean"     : three_arg_src_clean,
	"dir_clean"     : three_arg_dir_clean,
	"move_unlinked" : three_arg_move_unlinked,
	"auto_clean"    : three_arg_auto_clean,
	# "h_fix"         : three_arg_h_fix,
	"phash_clean"   : three_arg_phash_clean,

}



def printHelp():
	for help_str in help_strings:
		print(help_str)

	undoc_1 = [key for key in single_arg_funcs.keys() if not any([key in line for line in help_strings])]
	undoc_2 = [key for key in double_arg_funcs.keys() if not any([key in line for line in help_strings])]
	undoc_3 = [key for key in triple_arg_funcs.keys() if not any([key in line for line in help_strings])]
	undoc = {
		'1' : undoc_1,
		'2' : undoc_2,
		'3' : undoc_3,
	}
	if any(undoc.values()):
		print("")
		print("*********************************************************")
		print("Undocumented (FIX ME PLZ)")
		print("*********************************************************")

		keys = list(undoc.keys())
		keys.sort()
		for argnum in keys:
			fnames = undoc[argnum]
			if fnames:
				print("	Undocumented commands that take %s parameters:" % argnum)
				for fname in fnames:
					print("		%s" % fname)

	return


def parseOneArgCall(param):
	if param in single_arg_funcs:
		single_arg_funcs[param]()
	else:
		printHelp()
		print("ERROR")
		print("Unknown single_word arg: '%s'!" % param)

def parseTwoArgCall(cmd, val):
	if cmd in double_arg_funcs:
		double_arg_funcs[cmd](val)

	else:
		printHelp()
		print("ERROR")
		print("Did not understand command!")
		print("Sys.argv = ", sys.argv)


def parseThreeArgCall(cmd, arg1, arg2):
	if cmd in double_arg_funcs:
		triple_arg_funcs[cmd](arg1, arg2)

	else:
		print("ERROR")
		print("Did not understand command!")
		print("Sys.argv = ", sys.argv)

def parseFourArgCall(cmd, arg1, arg2, arg3):
	raise ValueError("Wat?")


def customHandler(dummy_signum, dummy_stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt


def parseCommandLine():
	signal.signal(signal.SIGINT, customHandler)
	if len(sys.argv) == 2:
		cmd = sys.argv[1].lower().replace("-", "_")
		parseOneArgCall(cmd)

	elif len(sys.argv) == 3:
		cmd = sys.argv[1].lower().replace("-", "_")
		val = sys.argv[2]
		parseTwoArgCall(cmd, val)

	elif len(sys.argv) == 4:

		cmd = sys.argv[1].lower().replace("-", "_")
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]
		parseThreeArgCall(cmd, arg1, arg2)

	elif len(sys.argv) == 5:

		cmd = sys.argv[1].lower().replace("-", "_")
		arg1 = sys.argv[2]
		arg2 = sys.argv[3]
		arg3 = sys.argv[4]
		parseFourArgCall(cmd, arg1, arg2, arg3)

	else:
		printHelp()

if __name__ == "__main__":
	print("Command line parse")
	parseCommandLine()

