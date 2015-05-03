from selenium import webdriver
import time, os, sys, subprocess

sites = ["http://www.wikipedia.org/",
		 "http://www.yahoo.com",
		 "http://www.facebook.com",
		 "http://www.google.com",
		 "http://www.youtube.com",
		 "http://www.live.com",
		 "http://www.blogspot.com",
		 "https://twitter.com/",
		 "http://www.amazon.com/",
		 "http://www.linkedin.com/",
		 "http://www.msn.com/",
		 "http://wordpress.com/",
		 "http://www.ebay.com/",
		 "http://craigslist.org",
		 "http://www.bing.com/",
		 "http://www.cnn.com/",
		 "http://espn.go.com/",
		 "http://go.com/",
		 ]

def clearDnsCache():
	p = subprocess.Popen(["dscacheutil", "-flushcache"])
	p.wait()
	return

class WebTester:
	def __init__(self, baseDir=None):
		if baseDir == None:
			baseDir = os.path.dirname(os.path.abspath(__file__))
		self.dir1 = os.path.join(baseDir, "1st")
		os.makedirs(self.dir1)
		self.profile1 = self._make_profile(self.dir1)
		self.browser1 = webdriver.Firefox(firefox_profile=self.profile1)
	def run(self, sites):
		f1 = open(os.path.join(self.dir1, "timings.txt"), "w")
		for site in sites:
			clearDnsCache()
			t0 = time.time()
			self.browser1.get(site)
			t1 = time.time()
			f1.write(site+"\t"+str(t1-t0)+"\n")
			time.sleep(3)
			clearDnsCache()
		f1.close()
	def quit(self):
		self.browser1.stop_client()
		self.browser1.quit()


	def _make_profile(self, baseDir):
		wd = os.path.dirname(os.path.abspath(__file__))
		profile = webdriver.firefox.firefox_profile.FirefoxProfile()
		profile.add_extension(os.path.join(wd,"plugins/firebug-1.9.1-fx.xpi"))
		profile.add_extension(os.path.join(wd,"plugins/netExport-0.8b21.xpi"))
		profile.add_extension(os.path.join(wd,"plugins/fireStarter-0.1a6.xpi"))
		profile.set_preference("extensions.firebug.currentVersion", "1.10.0a5")
		profile.set_preference("extensions.firebug.addonBarOpened",True)
		profile.set_preference('extensions.firebug.console.enableSites', True)
		profile.set_preference("extensions.firebug.allPagesActivation","on")
		profile.set_preference("extensions.firebug.previousPlacement", 1)
		profile.set_preference("extensions.firebug.onByDefault", True)
		profile.set_preference("extensions.firebug.defaultPanelName", "console")
		profile.set_preference('extensions.firebug.script.enableSites',True)
		profile.set_preference("extensions.firebug.net.enableSites", True)
		profile.set_preference('extensions.firebug.console.logLimit',50000)
		profile.set_preference('extensions.firebug.openInWindow',True)
		profile.set_preference("extensions.firebug.alwaysShowCommandLine","true")
		profile.set_preference("extensions.firebug.net.persistent", True)

		profile.set_preference("extensions.firebug.netexport.alwaysEnableAutoExport", True)
		profile.set_preference("extensions.firebug.netexport.autoExportToFile", True)
		profile.set_preference("extensions.firebug.netexport.autoExportToServer", False)
		outputDir = os.path.join(baseDir,"hars")
		os.makedirs(outputDir)
		profile.set_preference("extensions.firebug.netexport.defaultLogDir", outputDir)
		return profile


if __name__ == "__main__":
	baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results/web", sys.argv[1])
	for i in range(int(sys.argv[2])):
		print i
		clearDnsCache()
		time.sleep(1)
		browserTest = WebTester(os.path.join(baseDir, "run_"+str(i)))
		browserTest.run(sites)
		browserTest.quit()
