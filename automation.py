import os, sys, shlex

def createDir(direc):
	command = "mkdir "+direc
	#print "create dir for ", direc

	if not (os.path.exists(direc) and os.path.isdir(direc)):
		os.system(command) 
 
def runspeedtest():
 	sc = shlex.split("./speedtest-cli")
	print "\nSpeedTest: "
	sc = subprocess.check_output(sc)
	print sc
	return sc

def runping():
	pc = shlex.split("ping -c 10 www.google.com")
	print '\n Ping to Google'
	pc = subprocess.check_output(pc)
	print pc
	return pc

# Parse speedtest output and return [uploadspeed, downloadspeed]
def parsespeedtest(sdata):
	# Speedtest data
	us = None
	ds = None
	st = None
	try:
		#print "\nsdata: ", sdata
		sd = sdata.split("Download:")
		sd = sd[1]
		sd = sd.split("\n")
		ds = sd[0]
		ds = ds.replace(" ", "")
		ds = ds.replace("Mbit/s", "")
		us = sd[2]
		us = us.split("Upload: ")
		#print "us: ", us
		us = us[1]
		us = us.replace(" ", "")
		us = us.replace("Mbit/s", "")
		st = [float(us), float(ds)]
	except:
		pass

	return st

def parsepingoutput(sdata):
	return sum([ float(x.split(' ms')[0].strip()) for x in sdata.split('time=')[1:]])/20.0

bandwidths = ['500kb', '1mb', '10mb']
latencies = ['10ms','50ms', '100ms']

while True:
	for bw in bandwidths:
		bwcomm = 'tc qdisc add dev eth0 root handle 1:0 tbf rate '+bw
		os.system(bwcomm)
		for lat in latencies:
			labcomm = 'tc qdisc add dev eth0 root netem delay '+ lat
			os.system(labcomm)
			sc = runspeedtest()
			st = parsespeedtest(sc)
			print 'Current speeds are: download %s, upload %s' %(st[1], st[0])
			pc = runping()
			pingres = parsepingoutput(pc)
			print 'Current Latency to Google is %s' % (pingres)
			os.system('python firefox/WebTester.py')
