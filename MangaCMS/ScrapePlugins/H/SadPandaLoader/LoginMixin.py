
import settings
import copy

class ExLoginMixin(object):



	def checkLogin(self):

		checkPage = self.wg.getpage(r"https://forums.e-hentai.org/index.php")
		if not isinstance(checkPage, str):
			self.log.warning("Page isn't a string?")
			self.log.warning("Page size: %s, type: %s", len(checkPage), type(checkPage))
			with open("check-login-error.html", "wb") as fp:
				fp.write(getPage)

		if "Logged in as" in checkPage:
			self.log.info("Still logged in")
			return
		else:
			self.log.info("Whoops, need to get Login cookie")

		logondict = {
			"UserName"   : settings.sadPanda["login"],
			"PassWord"   : settings.sadPanda["passWd"],
			"referer"    : "https://forums.e-hentai.org/index.php?",
			"CookieDate" : "Log me in",
			"b"          : '',
			"bt"         : '',
			"submit"     : "Log me in"
			}

		getPage = self.wg.getpage(r"https://forums.e-hentai.org/index.php?act=Login&CODE=01", postData=logondict)
		if not isinstance(getPage, str):
			self.log.warning("Page isn't a string?")
			with open("login-error.html", "wb") as fp:
				fp.write(getPage)

		if "Username or password incorrect" in getPage:
			self.log.error("Login failed!")
			with open("pageTemp.html", "wb") as fp:
				fp.write(getPage)
		elif "You are now logged in as:" in getPage:
			self.log.info("Logged in successfully!")

		confdict = {

			'uh'          : 'y',                # New
			'xr'          : 'a',                # New
			'rx'          : '0',                # New
			'ry'          : '0',                # New
			'tl'          : 'r',                # New
			'ar'          : '0',                # New
			'dm'          : 'l',                # New
			'prn'         : 'n',                # New
			'f_doujinshi' : 'on',               # New
			'f_manga'     : 'on',               # New
			'f_artistcg'  : 'on',               # New
			'f_gamecg'    : 'on',               # New
			'f_western'   : 'on',               # New
			'f_non-h'     : 'on',               # New
			'f_imageset'  : 'on',               # New
			'f_cosplay'   : 'on',               # New
			'f_asianporn' : 'on',               # New
			'f_misc'      : 'on',               # New
			'favorite_0'  : 'Favorites+0',      # New
			'favorite_1'  : 'Favorites+1',      # New
			'favorite_2'  : 'Favorites+2',      # New
			'favorite_3'  : 'Favorites+3',      # New
			'favorite_4'  : 'Favorites+4',      # New
			'favorite_5'  : 'Favorites+5',      # New
			'favorite_6'  : 'Favorites+6',      # New
			'favorite_7'  : 'Favorites+7',      # New
			'favorite_8'  : 'Favorites+8',      # New
			'favorite_9'  : 'Favorites+9',      # New
			'fs'          : 'p',                # New
			'ru'          : 'RRGGB',            # New
			'xl_2048'     : 'on',               # New
			'xl_2049'     : 'on',               # New
			'xl_1034'     : 'on',               # New
			'xl_2058'     : 'on',               # New
			'xl_1044'     : 'on',               # New
			'xl_2068'     : 'on',               # New
			'xl_1054'     : 'on',               # New
			'xl_2078'     : 'on',               # New
			'xl_1064'     : 'on',               # New
			'xl_2088'     : 'on',               # New
			'xl_1074'     : 'on',               # New
			'xl_2098'     : 'on',               # New
			'xl_1084'     : 'on',               # New
			'xl_2108'     : 'on',               # New
			'xl_1094'     : 'on',               # New
			'xl_2118'     : 'on',               # New
			'xl_1104'     : 'on',               # New
			'xl_2128'     : 'on',               # New
			'xl_1114'     : 'on',               # New
			'xl_2138'     : 'on',               # New
			'xl_1124'     : 'on',               # New
			'xl_2148'     : 'on',               # New
			'xl_1134'     : 'on',               # New
			'xl_2158'     : 'on',               # New
			'xl_1144'     : 'on',               # New
			'xl_2168'     : 'on',               # New
			'xl_1154'     : 'on',               # New
			'xl_2178'     : 'on',               # New
			'xl_1278'     : 'on',               # New
			'xl_2302'     : 'on',               # New
			'xl_1279'     : 'on',               # New
			'xl_2303'     : 'on',               # New
			'xu'          : '',                 # New
			'rc'          : '3',                # New
			'lt'          : 'm',                # New
			'ts'          : 'm',                # New
			'tr'          : '2',                # New
			'cs'          : 'a',                # New
			'sc'          : '0',                # New
			'to'          : 'a',                # New
			'pn'          : '0',                # New
			'hh'          : '',                 # New
			'sa'          : 'y',                # New
			'oi'          : 'b55ba7',           # New
			'apply'       : 'Apply',            # New

			}
		headers = {
			'Referer': 'http://e-hentai.org/uconfig.php',
			'Host': 'e-hentai.org'
		}
		getPage = self.wg.getpage(r"http://e-hentai.org/uconfig.php", postData=confdict, addlHeaders=headers)

		self.permuteCookies()
		self.wg.saveCookies()

	# So exhen uses some irritating cross-site login hijinks.
	# Anyways, we need to copy the cookies for e-hentai to exhentai,
	# so we iterate over all cookies, and duplicate+modify the relevant
	# cookies.
	def permuteCookies(self):
		self.log.info("Fixing cookies")
		for cookie in self.wg.cj:
			if (
					"ipb_member_id" in cookie.name or
					"ipb_pass_hash" in cookie.name or
					"uconfig"       in cookie.name or
					'hath_perks'    in cookie.name
					):

				dup = copy.copy(cookie)
				dup.domain = 'exhentai.org'

				self.wg.addCookie(dup)


	# MOAR checking. We load the root page, and see if we have anything.
	# If we get an error, it means we're being sadpanda'ed (because it serves up a gif
	# rather then HTML, which causes getSoup() to error), and we should abort.
	def checkExAccess(self):
		try:
			self.wg.getSoup(self.urlBase)
			return True
		except ValueError:
			return False
