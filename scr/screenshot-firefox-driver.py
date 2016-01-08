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
import signal

####Configure Info######

fetchedurls = []

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
	os.kill(pid, signal.SIGKILL)
	parent = psutil.Process(pid)
	for child in parent.children(recursive=True):  # or parent.children() for recursive=False
		#child.kill()
		os.kill(child.pid, signal.SIGKILL)
	os.kill(pid, signal.SIGKILL)
	#parent.kill()

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


def repeatedVisitWebPage(args):

        configureFilePath = args.configurepath
        times = args.times
        url = args.url

	logger.debug("Start visiting web page %s for %d times..."%(args.url,args.times))
	data = readConfigure(configureFilePath)
	if data == None:
		logger.error("failed to read configure file")
		return

	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 9090))
    	serversocket.listen(1)
	#serversocket.setblocking(0)
	serversocket.settimeout(500)
	for i in range(times):		
		profile = webdriver.FirefoxProfile(data['firefoxProfilePathWithProxy'])
		browser = webdriver.Firefox(profile)
                browser.maximize_window()
		if browser == None:
			logger.error("failed to create firefox instance")
			return 
		o = urlparse(url)
		host = o.netloc

		#10 minutes
		browser.set_page_load_timeout(500)

		try:
			logName = host + "_" + str(i)
			logger.debug("  start running mitmproxy")

			p, outFile, errFile = runMitmproxy(data['mitmproxyScriptPath'], args.dir, args.low, args.high, args.secondsbetweenrequests, logName)
			logger.debug("  start browsing %d time and store to file %s"%(i,logName) )
			#time.sleep(2)
			logger.debug("  opening tab in browser")	
			openNewTab(browser)

			logger.debug("  calling browser.get(url) asynchronously")
			if url in fetchedurls:			
				fetchedurls.remove(url)			
			threading.Thread(target=call_getBrowser, args=[browser, url, p, outFile, errFile]).start()

			logger.debug("  waiting on signal")
			#serversocket.setblocking(0)
			if args.high > 0:			
				connection, address = serversocket.accept()
				#connection.settimeout(10)
                        	logger.debug("  accepted a connection")
       			while True:
				if url in fetchedurls:
					logger.debug('Completed fetching')
					break
				
				if args.high >0:
                			buf = connection.recv(64)
                			if len(buf) > 0 and "done" in buf:
						logger.debug('Got signal')
			        		break		
			if args.high > 0:			
				connection.close()

			sendExitSignalToProxy()
			terminateMitmproxy(p, outFile, errFile)
			logger.debug("  done terminating mitmproxy")

  			logger.debug("  closing browser")
			browser.quit()
			logger.debug("  done browsing %d time and store to file %s"%(i,logName) )
			time.sleep(2);
		except Exception as e:
			logger.error("error [%s] in repeatedVisitWebPage reason: %s. start cleaning states..."%(logName,str(e)) )

			sendExitSignalToProxy()
			terminateMitmproxy(p, outFile, errFile)
			logger.debug("  [IN EXCEPTION HANDLER] done terminating mitmproxy")
			browser.quit()
			logger.debug("  [IN EXCEPTION HANDLER] done closing current tab")
			time.sleep(2)
			
			
def call_getBrowser(browser, url, p, outFile, errFile):
	try:	
		starttime = time.time()
		browser.get(url)
		endtime = time.time()
		loading_time = endtime - starttime
		open('fetchingtime.txt', 'a').write('\n'+url+'\t'+str(starttime)+'\t'+str(endtime)+'\t'+str(loading_time))
		logger.debug('fetched........')	
	except Exception as e:  #probably on timeout
		logger.debug('error in get browser.....')
	fetchedurls.append(url)
	logger.debug('added to fetched'+str(fetchedurls))

def readHostList(filePath):
	f = open(filePath)
	data = []
	for line in f:
		line = line.strip()
		data.append(line)
	return data

def parse_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('--configurepath','-c', help='the path of configure file')
	parser.add_argument('--dir','-d', help='directory of log files')
	parser.add_argument('--times','-t',type=int, help='the times to browse')
	parser.add_argument('--url','-u', help='the url of the trace')
	parser.add_argument('--high','-hi',type=float, help='the picture similarity must be below this value')
	parser.add_argument('--low','-lo', type=float, help='the picture similarity must be above this value')
	parser.add_argument('--secondsbetweenrequests','-s', help='delay in seconds between requests allowed by proxy')

	args = parser.parse_args()
	try:
		o = urlparse(args.url)
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

	if not os.path.exists("./results"):
		os.makedirs("./results")
	
	args = parse_arguments()
	if not args:
		return

	logger.debug("repeated visit %s for %d times with proxy" % (args.url,args.times))
	repeatedVisitWebPage(args)


if __name__ == "__main__":
	main()
	
