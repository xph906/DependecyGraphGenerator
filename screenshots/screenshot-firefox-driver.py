from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from urlparse import urlparse
import time
import requests
import logging
import sys
import json
import os
import subprocess
import psutil
import argparse
import socket
import threading

####Configure Info######

logger = logging.getLogger('firefox-driver')

#########################################
#			Selenium Utilities			#
#########################################
def openNewTab(browser):
	if sys.platform == "darwin":
		ActionChains(browser).send_keys(Keys.COMMAND, "t").perform()
		ActionChains(browser).send_keys(Keys.COMMAND, "t").perform()
	elif sys.platform == "linux2":
		#ActionChains(browser).send_keys(Keys.CONTROL, "t").perform()
		logger.debug( "skipping this key command for now")
		#ActionChains(browser).send_keys(Keys.CONTROL, "t").perform()
	else:
		logger.error("openNewTab unsupported OS: %s"%sys.platform)

def closeCurrentTab(browser):
	if sys.platform == "darwin":
		browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
	elif sys.platform == "linux2":
		#browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
		logger.debug("skipping closing for now")
	else:
		logger.error("closeCurrentTab unsupported OS: %s"%sys.platform)

def testSelenium():
	profile = webdriver.FirefoxProfile(FirefoxProfileName)
	browser = webdriver.Firefox(profile)

	openNewTab()
	browser.get('http://www.cnn.com/')
	closeCurrentTab()
	time.sleep(1)

	openNewTab()
	browser.get('http://www.yahoo.com/')
	browser.quit()
	logger.info("Done")

#########################################
#			Process Utilities			#
#########################################
def killProcessAndChildren(pid):
	parent = psutil.Process(pid)
	for child in parent.children(recursive=True):  # or parent.children() for recursive=False
		child.kill()
	parent.kill()

def runBackgroundProcess(args,outFile,errFile):
	try:
		p = subprocess.Popen(args,stdout=outFile,stderr=errFile)
		return p
	except Exception as e:
		logger.error("error runBackgroundProcess due to: %s" % str(e))

def runMitmproxy(scriptPath, logDir, thresholdLow, thresholdHigh, secondsBetweenRequests, logFile):
	param = '"\"%s %s %s %s %s %s\""'%(scriptPath, logDir, thresholdLow, thresholdHigh, secondsBetweenRequests, logFile)

	args = ['mitmproxy','-s',param]
	outFileName = os.path.join(logDir, 'stdout.txt')
	outFile = open(outFileName,'w+')
	errFileName = os.path.join(logDir,'stderr.txt')
	errFile = open(errFileName,'w+')
	logger.debug("prepare to run mitmproxy %s"%(' '.join(args),))
	p = runBackgroundProcess(args, outFile, errFile)
	errFile.write("write sth for test....\n");
	time.sleep(3)
	p.poll()
	if p.returncode == None:
		logger.debug("successfully run mitmproxy with pid %d "%p.pid)
		return p, outFile, errFile
	else:
		logger.error("failed to run mitmproxy %d"%p.returncode)
		return None, None, None

def terminateMitmproxy(proxyProcess, outFile, errFile):
	try:
		if outFile and not outFile.closed:
			outFile.close()
		if errFile and not errFile.closed:
			errFile.close()
		if proxyProcess != None:
			killProcessAndChildren(proxyProcess.pid)
			time.sleep(2)
	except Exception as e:
		logger.error("failed to terminate mitmproxy "+str(e))

#########################################
#			Other Utilities				#
#########################################

def sendExitSignalToProxy(port=8080):
	proxies = {
		"http": "http://localhost:8080",
		"https": "http://localhost:8080",
	}
	url = "http://localhost/commands/exit"
	try:
		r = requests.get(url,timeout=5,proxies=proxies)
		if r.text.strip() == "done":
			logger.debug("command EXIT has been received")
	except Exception as e:
		logger.error("error "+str(e))

def readConfigure(file_path):
	try:
		json_file = open(file_path)
		data = json.load(json_file)
		json_file.close()
		return data
	except Exception as e:
	    logger.error("failed to parse configure file "+file_path+" "+str(e))
	    return None


#########################################
#			Other Utilities				#
#########################################

def repeatedVisitWebPage(url,times,configureFilePath,logFileBaseName=None,useProxy=True):
	logger.debug("Start visiting web page %s for %d times..."%(url,times))
	data = readConfigure(configureFilePath)
	if data == None:
		logger.error("failed to read configure file")
		return
	
	if useProxy:
		profile = webdriver.FirefoxProfile(data['firefoxProfilePathWithProxy'])
	else:
		profile = webdriver.FirefoxProfile(data['firefoxProfilePathWithoutProxy'])
	browser = webdriver.Firefox(profile)
	if browser == None:
		logger.error("failed to create firefox instance")
		return 
	o = urlparse(url)
	host = o.netloc;
	if logFileBaseName == None:
		logFileBaseName = host+'_%d'
	else:
		logFileBaseName += '_%d'
	browser.set_page_load_timeout(600)
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 9090))
    	serversocket.listen(1)
	#openNewTab(browser)
	for i in range(times):
		try:
			logName = logFileBaseName % i
			if useProxy:
				logger.debug("  start running mitmproxy");
				p, outFile, errFile = runMitmproxy(data['mitmproxyScriptPath'], data['logDir'], data['thresholdLow'], data['thresholdHigh'], data['secondsBetweenRequests'], logName)
				logger.debug("  start browsing %d time and store to file %s"%(i,logName) )
			time.sleep(2)
			logger.debug("  opening tab in browser")	
			openNewTab(browser)

			logger.debug("  calling browser.get(url) asynchronously")
			threading.Thread(target=call_getBrowser, args=[browser, url]).start()

			logger.debug("  waiting on signal")
			connection, address = serversocket.accept()
                        logger.debug("  accepted a connection")
       			while True:
                		buf = connection.recv(64)
                		if len(buf) > 0 and "done" in buf:
			        	break		

			connection.close()

  			logger.debug("  closing browser")
			closeCurrentTab(browser)
			logger.debug("  done browsing %d time and store to file %s"%(i,logName) )
			if useProxy:
				sendExitSignalToProxy()
				terminateMitmproxy(p, outFile, errFile)
				logger.debug("  done terminating mitmproxy")
			time.sleep(2);
		except Exception as e:
			logger.error("error [%s] in repeatedVisitWebPage reason: %s. start cleaning states..."%(logName,str(e)) )
			closeCurrentTab(browser)
			logger.debug("  [IN EXCEPTION HANDLER] done closing current tab")
			if useProxy:
				sendExitSignalToProxy()
				terminateMitmproxy(p, outFile, errFile)
				logger.debug("  [IN EXCEPTION HANDLER] done terminating mitmproxy")
			time.sleep(2);
			
			
def call_getBrowser(browser, url):
	browser.get(url)

def readHostList(filePath):
	f = open(filePath)
	data = []
	for line in f:
		line = line.strip()
		data.append(line)
	return data

def parse_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('--function','-f', help='the function to execute')
	parser.add_argument('--prefix','-p', help='prefix of file names')
	parser.add_argument('--configurepath','-c', help='the path of configure file')
	parser.add_argument('--dir','-d', help='directory of log files')
	parser.add_argument('--times','-t',type=int, help='the times of browsing a file')
	parser.add_argument('--timeout','-to',type=int, help='the timeout of loading a page')
	parser.add_argument('--firsturl','-fu', help='the first url of each trace')
	#parser.add_argument('--os','-os', help='the operating system type')
	#parser.add_argument('--lasturl','-lu', help='the last url of each trace')
	parser.add_argument('--commonhostlist','-ch', help='the path of valid object url list')
	args = parser.parse_args()
	try:
		o = urlparse(args.firsturl)
	except Exception as e:
		parser.print_help()
		return None
	return args

def main():
	hdlr = logging.FileHandler('driver.log')
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr) 
	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(formatter)
	logger.addHandler(consoleHandler)
	logger.setLevel(logging.DEBUG)
	
	args = parse_arguments()
	if not args:
		return
	if args.function == "normalvisit":
		logger.debug("repeated visit %s for %d times without proxy" % (args.firsturl,args.times))
		repeatedVisitWebPage(args.firsturl,args.times,args.configurepath,args.prefix,useProxy=False)
	elif args.function == "proxyvisit":
		logger.debug("repeated visit %s for %d times with proxy" % (args.firsturl,args.times))
		repeatedVisitWebPage(args.firsturl,args.times,args.configurepath,args.prefix,useProxy=True)


if __name__ == "__main__":
	main()
	
