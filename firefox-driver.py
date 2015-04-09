from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import requests
import logging
import sys

logger = logging.getLogger('firefox-driver')

def openNewTab(browser):
	ActionChains(browser).send_keys(Keys.COMMAND, "t").perform()
	ActionChains(browser).send_keys(Keys.COMMAND, "t").perform()

def closeCurrentTab(browser):
	browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')

def testSelenium():
	profile = webdriver.FirefoxProfile("/Users/a/Library/Application Support/Firefox/Profiles/dp02h9ua.nocacheuser")
	browser = webdriver.Firefox(profile)

	openNewTab()
	browser.get('http://www.cnn.com/')
	closeCurrentTab()
	time.sleep(1)

	openNewTab()
	browser.get('http://www.yahoo.com/')
	browser.quit()
	logger.info("Done")

def sendExitSignalToProxy(port=8080):
	proxies = {
		"http": "http://localhost:8080",
		"https": "http://localhost:8080",
	}
	url = "http://localhost/commands/exit"
	try:
		r = requests.get(url,timeout=5,proxies=proxies)
		if r.text.strip() == "done":
			print "command EXIT has been received"
	except Exception as e:
		logger.error("error "+str(e))

def repeatedVisitWebPage(url,times):
	logger.debug("Start visiting web page %s for %d times..."%(url,times))
	profile = webdriver.FirefoxProfile("/Users/a/Library/Application Support/Firefox/Profiles/dp02h9ua.nocacheuser")
	browser = webdriver.Firefox(profile)
	for i in range(times):
		try:
				
			logger.debug("  start browsing %d time"%i);	
			openNewTab(browser)
			browser.get(url)
			closeCurrentTab(browser)
			logger.debug("  done browsing %d time"%i);
			#sendExitSignalToProxy()
			time.sleep(2);
		except Exception as e:
			logger.error("error in repeatedVisitWebPage reason: %s"%str(e))
	browser.quit()

def main():
	hdlr = logging.FileHandler('driver.log')
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)
	#logger.addHandler(hdlr) 
	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(formatter)
	logger.addHandler(consoleHandler)
	logger.setLevel(logging.DEBUG)
	repeatedVisitWebPage(sys.argv[1],10)

if __name__ == "__main__":
	main()
	