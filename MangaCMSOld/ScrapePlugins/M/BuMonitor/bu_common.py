
import time
import random

import urllib.parse
import bs4
import WebRequest
import ChromeController

import settings



def getItemChromium(wg, log, itemUrl):
	log.info("Fetching page for URL: '%s' with Chromium" % itemUrl)

	with wg._chrome_context('http://www.google.com', extra_tid=None) as cr:

		wg._syncIntoChromium(cr)

		response = cr.blocking_navigate_and_get_source(itemUrl, timeout=wg.navigate_timeout_secs)

		raw_url = cr.get_current_url()
		fileN = urllib.parse.unquote(urllib.parse.urlparse(raw_url)[2].split("/")[-1])
		fileN = bs4.UnicodeDammit(fileN).unicode_markup

		wg._syncOutOfChromium(cr)

	# Probably a bad assumption
	if response['binary']:
		mType = "application/x-binary"
	else:
		mType = "text/html"

	# Use the new interface that returns the actual type
	if 'mimetype' in response:
		mType = response['mimetype']

	# So, wg._cr.page_source appears to be the *compressed* page source as-rendered. Because reasons.
	content = response['content']

	return content, fileN, mType

def fetch_retrier(soup=True, wg=None, log=None, *args, **kwargs):
	assert wg
	assert log

	# if 'addlHeaders' not in kwargs:
	# 	kwargs['addlHeaders'] = {}


	# kwargs['addlHeaders']['Origin']                    = 'https://www.mangaupdates.com'
	# kwargs['addlHeaders']['Upgrade-Insecure-Requests'] = 1
	# kwargs['addlHeaders']['DNT']                       = 1
	# kwargs['addlHeaders']['Connection']                = "keep-alive"


	for x in range(9999):
		try:
			if not args and len(kwargs) == 1 and 'requestedUrl' in kwargs:
				wg.navigate_timeout_secs = 40
				content, fileN, mType = getItemChromium(wg, log, itemUrl=kwargs['requestedUrl'])
				ret = content
			else:
				ret = wg.getpage(*args, **kwargs)

			if soup:
				ret = WebRequest.as_soup(ret)

			time.sleep(5)
			return ret

		except (WebRequest.FetchFailureError, ChromeController.ChromeResponseNotReceived) as e:
			if x > 20:
				raise
			sleep_interval = 4 * (x+1)
			log.warning("Fetching page failed. Retrying after %s seconds.", sleep_interval)
			time.sleep(sleep_interval)


def checkLogin(log, wg):
	log.info("Validating login state")

	logondict = {
			"username" : settings.buSettings["login"],
			"password" : settings.buSettings["passWd"],
			"act"      : "login",
			'x'        : random.randint(0, 44),
			'y'        : random.randint(0, 19),
		}


	with wg._chrome_context('http://www.google.com', extra_tid=None) as cr:

		response = cr.blocking_navigate_and_get_source("https://www.google.com", timeout=wg.navigate_timeout_secs)

		for x in range(9999):
			try:
				wg._syncIntoChromium(cr)

				itemUrl = "https://www.mangaupdates.com/login.html"
				log.info("Fetching page for URL: '%s' with Chromium" % itemUrl)


				response = cr.blocking_navigate_and_get_source(itemUrl, timeout=wg.navigate_timeout_secs)

				wg._syncOutOfChromium(cr)

				if "You are currently logged in as" in response['content']:
					log.info("Still logged in")
					return
				else:
					log.info("Whoops, need to get Login cookie")

				time.sleep(5)
				break

			except (WebRequest.FetchFailureError, ChromeController.ChromeResponseNotReceived) as e:
				if x > 20:
					raise
				sleep_interval = 4 * (x+1)
				log.warning("Fetching page failed. Retrying after %s seconds.", sleep_interval)
				log.warning("Exception: %s", e)
				time.sleep(sleep_interval)



		for x in range(9999):
			try:

				log.info("Fetching page for URL: '%s' with Chromium" % itemUrl)

				raw_url = cr.get_current_url()
				if "www.mangaupdates.com" not in raw_url:
					raise RuntimeError("Wat?")

				log.info("Executing login via injected JS")
				cr.execute_javascript('''
 /**
 * sends a request to the specified url from a form. this will change the window location.
 * @param {string} path the path to send the post request to
 * @param {object} params the paramiters to add to the url
 * @param {string} [method=post] the method to use on the form
 */

function post(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
}

					''', args=['https://www.mangaupdates.com/login.html', logondict])

				time.sleep(10)

				log.info("Checking new login state")
				response = cr.blocking_navigate_and_get_source(itemUrl, timeout=wg.navigate_timeout_secs)

				fileN = urllib.parse.unquote(urllib.parse.urlparse(raw_url)[2].split("/")[-1])
				fileN = bs4.UnicodeDammit(fileN).unicode_markup

				wg._syncOutOfChromium(cr)

				# So, wg._cr.page_source appears to be the *compressed* page source as-rendered. Because reasons.
				page_content = response['content']


				time.sleep(5)
				break

			except (WebRequest.FetchFailureError, ChromeController.ChromeResponseNotReceived) as e:
				if x > 20:
					raise
				sleep_interval = 4 * (x+1)
				log.warning("Fetching page failed. Retrying after %s seconds.", sleep_interval)
				log.warning("Exception: %s", e)
				time.sleep(sleep_interval)

	if "You are currently logged in as" in page_content:
		log.info("Logged in successfully!")
	else:
		log.error("Login failed!")
		raise ValueError("Cannot login to MangaUpdates. Is your login/password valid?")

	wg.saveCookies()
