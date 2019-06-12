

import colorsys
import MangaCMS.activePlugins



additional_manga = [
		{'key' : "mb",      'name' : "MangaBaby",   'type' : 'Manga-defunct', 'feedLoader'    : None, 'contentLoader' : None, 'runner' : None},
		{'key' : None,      'name' : "Mt Mon",      'type' : 'Manga-defunct', 'feedLoader'    : None, 'contentLoader' : None, 'runner' : None},
]
additional_hentai = [
]
additional_other = [

		{'key' : None,      'name' : "MU Mon",      'type' : 'Info',          'feedLoader'    : None, 'contentLoader' : None, 'runner' : None},
]


# all_scrapers = [ ]

# old_all = [
# 		{'dbKey' : "sk",      'name' : "Starkana",    'dictKey' : "SkLoader",         'cssClass' : "skId",    'showOnHome' : False, 'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "cz",      'name' : "Crazy's",     'dictKey' : "CzLoader",         'cssClass' : "czId",    'showOnHome' : True,  'renderSideBar' : False, 'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "bt",      'name' : "Batoto",      'dictKey' : "BtLoader",         'cssClass' : "btId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "jz",      'name' : "Japanzai",    'dictKey' : "JzLoader",         'cssClass' : "jzId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mc",      'name' : "MangaCow",    'dictKey' : "McLoader",         'cssClass' : "mcId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "cx",      'name' : "CXC Scans",   'dictKey' : "CxLoader",         'cssClass' : "cxId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mh",      'name' : "Manga Here",  'dictKey' : "MangaHere",        'cssClass' : "mhId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mj",      'name' : "MangaJoy",    'dictKey' : "MjLoader",         'cssClass' : "mjId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "rh",      'name' : "RedHawk",     'dictKey' : "RhLoader",         'cssClass' : "rhId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "lm",      'name' : "LoneManga",   'dictKey' : "LmLoader",         'cssClass' : "lmId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "wt",      'name' : "Webtoon",     'dictKey' : "WtLoader",         'cssClass' : "wtId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "dy",      'name' : "Dynasty",     'dictKey' : "DyLoader",         'cssClass' : "dyId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "ki",      'name' : "KissManga",   'dictKey' : "KissLoader",       'cssClass' : "kiId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "cr",      'name' : "CrunchyRoll", 'dictKey' : "CrunchyRoll",      'cssClass' : "crId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "rs",      'name' : "Roselia",     'dictKey' : "RoseliaLoader",    'cssClass' : "rsId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "se",      'name' : "Sense",       'dictKey' : "SenseLoader",      'cssClass' : "seId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "sj",      'name' : "ShoujoSense", 'dictKey' : "ShoujoSense",      'cssClass' : "sjId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "vx",      'name' : "Vortex",      'dictKey' : "VortexLoader",     'cssClass' : "vxId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "th",      'name' : "TwistedHel",  'dictKey' : "TwistedHel",       'cssClass' : "thId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "cs",      'name' : "Casanova",    'dictKey' : "Casanova",         'cssClass' : "csId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "ms",      'name' : "MangaStrm",   'dictKey' : "MsLoader",         'cssClass' : "msId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mp",      'name' : "Mangatopia",  'dictKey' : "MangatopiaLoader", 'cssClass' : "mpId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "wr",      'name' : "WebTnsRdr",   'dictKey' : "WrLoader",         'cssClass' : "wrId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "irc-irh", 'name' : "IRC XDCC",    'dictKey' : "IrcEnqueue",       'cssClass' : "ircId",   'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "irc-trg", 'name' : "IRC Trigger", 'dictKey' : "IrcEnqueue",       'cssClass' : "ircId",   'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "kw",      'name' : "Kawaii Scans",'dictKey' : "kawaii",           'cssClass' : "kawaii",  'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "sura",    'name' : "Sura's Place",'dictKey' : "sura",             'cssClass' : "sura",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mbx",     'name' : "MangaBox",    'dictKey' : "mbx",              'cssClass' : "mbx",     'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "gos",     'name' : "GosLoader",   'dictKey' : "gos",              'cssClass' : "gos",     'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "ym",      'name' : "YoManga",     'dictKey' : "ym",               'cssClass' : "ym",      'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "ms",      'name' : "MangaStrm",   'dictKey' : "ms",               'cssClass' : "ms",      'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "meraki",  'name' : "Meraki",      'dictKey' : "meraki",           'cssClass' : "meraki",  'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mk",      'name' : "Madokami",    'dictKey' : "MkLoader",         'cssClass' : "mkId",    'showOnHome' : False, 'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mdx",     'name' : "MangaDex",    'dictKey' : "MangaDex",         'cssClass' : "mdxId",   'showOnHome' : False, 'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		{'dbKey' : "mzk",     'name' : "MangaZuki",   'dictKey' : "MangaZuki",        'cssClass' : "mzkId",   'showOnHome' : False, 'renderSideBar' : True,  'genRow' : True,  'type' : 'Manga'         },
# 		############################################################################# ##########################
# 		############################################################################# ##########################
# 		{'dbKey' : "djm",     'name' : "DjMoe",       'dictKey' : "DjMoe",            'cssClass' : "djmId",   'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "pu",      'name' : "Pururin",     'dictKey' : "Pururin",          'cssClass' : "puId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "sp",      'name' : "ExHentai",    'dictKey' : "SadPanda",         'cssClass' : "spId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "hb",      'name' : "H-Browse",    'dictKey' : "H-Browse",         'cssClass' : "hbId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "fk",      'name' : "Fakku",       'dictKey' : "FkLoader",         'cssClass' : "fkId",    'showOnHome' : False, 'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "nh",      'name' : "NHentai",     'dictKey' : "NHentai",          'cssClass' : "nhId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "em",      'name' : "ExHenMado",   'dictKey' : "EmLoader",         'cssClass' : "emId",    'showOnHome' : True,  'renderSideBar' : False, 'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "ta",      'name' : "Tadano",      'dictKey' : "Tadanohito",       'cssClass' : "taId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "exArch",  'name' : "ExArch",      'dictKey' : "ExArchive",        'cssClass' : "exArId",  'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "hit",     'name' : "Hitomi",      'dictKey' : "Hitomi",           'cssClass' : "hitId",   'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "dol",     'name' : "DoujinOnline",'dictKey' : "DoujinOnline",     'cssClass' : "dolId",   'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "asmh",    'name' : "ASMHentai",   'dictKey' : "ASMHentai",        'cssClass' : "asmhId",  'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "h2r",     'name' : "Hentai2R",    'dictKey' : "Hentai2R",         'cssClass' : "h2rId",   'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 		{'dbKey' : "ts",      'name' : "Tsumino",     'dictKey' : "Tsumino",          'cssClass' : "tsId",    'showOnHome' : True,  'renderSideBar' : True,  'genRow' : True,  'type' : 'Porn'          },
# 	]


def tupToHSV(tup):
	r, g, b = (var*(1.0/256) for var in tup)
	return colorsys.rgb_to_hsv(r, g, b)

def hsvToHex(ftup):
	ftup = colorsys.hsv_to_rgb(*ftup)
	r, g, b = (max(0, min(int(var*256), 255)) for var in ftup)
	ret = "#{r:02x}{g:02x}{b:02x}".format(r=r, g=g, b=b)
	return ret

# I don't want to have to add all of numpy as a dependency just to get linspace,
# so we duplicate it here.
def linspace(a, b, n=100):
	if n < 2:
		return [b]
	diff = (float(b) - a)/(n - 1)
	ret = [diff * i + a  for i in range(n)]
	return ret


manga_scrapers = []
all_scrapers = []
hentai_scrapers = []
other_scrapers = []

items = list(MangaCMS.activePlugins.PLUGIN_MAP.items())
items.sort()

for plugin_name, plugin in items:
	if 'is_h' in plugin:
		if plugin["is_h"] == True:
			plugin['type'] = "Hentai"
			hentai_scrapers.append(plugin)
			all_scrapers.append(plugin)
		elif plugin['is_h'] == False:
			plugin['type'] = "Manga"
			manga_scrapers.append(plugin)
			all_scrapers.append(plugin)
	else:
		plugin['type'] = "Info"
		other_scrapers.append(plugin)
		all_scrapers.append(plugin)

for plugin in additional_manga:
	manga_scrapers.append(plugin)
	all_scrapers.append(plugin)
for plugin in additional_hentai:
	hentai_scrapers.append(plugin)
	all_scrapers.append(plugin)
for plugin in additional_other:
	other_scrapers.append(plugin)
	all_scrapers.append(plugin)

s_base, v_base = 0.35, 0.95
print("All scrapers:")
print(all_scrapers)

for keyset in [manga_scrapers, hentai_scrapers, other_scrapers, all_scrapers]:
	hues = linspace(0.0, 1.0, n=len(keyset)+1)
	keyset.sort(key=lambda x: str(x['key']))
	for item_dict in keyset:
		h = hues.pop()
		baseC  = (h,s_base,v_base)
		light1 = (h,s_base-0.05,v_base+0.2)
		light2 = (h,s_base-0.15,v_base+0.2)

		item_dict["baseColour"] = hsvToHex(baseC)
		item_dict["evenRow"] = hsvToHex(light1)
		item_dict["oddRow"] = hsvToHex(light2)
		item_dict["renderSideBar"] = item_dict['type'] in ['Manga', 'Hentai']

		item_dict['css_class'] = str(item_dict['key']) + "_id"

manga_scrapers.sort(key=lambda x: x['name'])
hentai_scrapers.sort(key=lambda x: x['name'])
other_scrapers.sort(key=lambda x: x['name'])

scraper_dict = {
	scrape['name'] : scrape for scrape in manga_scrapers + hentai_scrapers + other_scrapers
}