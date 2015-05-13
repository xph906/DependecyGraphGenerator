import subprocess
import shlex
import sys
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
import time

def automate_driver(file_name):
    driver = shlex.split("python firefox-driver.py -f proxyvisit -fu http://www.wsj.com -t 15 -c air_configure -p WSJ")
    if subprocess.call(driver) != 0:
    	sys.exit()
    
    commonurl = shlex.split("python LogAnalysis.py -f getcommonurl -d logs -p WSJ -ho wsjHostList")
    subprocess.call(commonurl)

    graph = shlex.split("python LogAnalysis.py -f generategraph -p WSJ -d ./logs/ -fu http://www.wsj.com/ -go wsjGraph -lu http://video-api.wsj.com/api-video/player/v2/css/wsjvideo.min.css -c wsjHostList")
    subprocess.call(graph)

def automate_analyze(host_name, graph_name, last_url, bandwidth):
    # setting up bandwidth...
    dnctl = shlex.split("dnctl pipe 1 config bw 300KByte/s queue 10Kbytes")
    subprocess.call(dnctl)
    #dummynet = shlex.split("echo \"dummynet in all pipe 1\" >> /etc/pf.conf")
    #subprocess.call(dummynet)


    # collecting data...
    listen = shlex.split("sudo /opt/bro/bin/bro -i en0 -C broscript/httpinfo.bro")
    f = open("broscript/test.txt", "w")
    background = subprocess.Popen(listen, stdout = f)

    url = "http://www.wsj.com"
    profile = webdriver.FirefoxProfile("/Users/yanghu/Library/Application Support/Firefox/Profiles/y0900nx6.withoutProxy")
    browser = webdriver.Firefox(profile)
    
    openNewTab(browser)
    browser.get(url)

    time.sleep(1)
    background.terminate()
    f.close()
    closeCurrentTab(browser)
    browser.quit()
   
    # getting latency and output
    output = open("%dkb_output.txt" % bandwidth, "w")
    analyze = shlex.split("python LogAnalysis.py -f analyzebrolog -fu http://www.wsj.com/ -lu " + last_url + " -gi " + graph_name + " -c " + host_name + " -b broscript/test.txt")
    subprocess.call(analyze, stderr=output)
    
def openNewTab(browser):
	if sys.platform == "darwin":
		ActionChains(browser).send_keys(Keys.COMMAND, "t").perform()
		ActionChains(browser).send_keys(Keys.COMMAND, "t").perform()
	elif sys.platform == "linux2":
		ActionChains(browser).send_keys(Keys.CONTROL, "t").perform()
		ActionChains(browser).send_keys(Keys.CONTROL, "t").perform()
	else:
		logger.error("openNewTab unsupported OS: %s"%sys.platform)

def closeCurrentTab(browser):
	if sys.platform == "darwin":
		browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
	elif sys.platform == "linux2":
		browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
	else:
		logger.error("closeCurrentTab unsupported OS: %s"%sys.platform)
    

if __name__ == '__main__':
    #file_name = sys.argv[1]
    host_name = sys.argv[1]
    graph_name = sys.argv[2]
    last_url = "http://video-api.wsj.com/api-video/player/v2/css/wsjvideo.min.css"
    
    #automate_driver(file_name)
    
    #bandwidth = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
    bandwidth = [10, 20, 30]
    for i in bandwidth:
        #i = 10
        automate_analyze(host_name, graph_name, last_url, i)
