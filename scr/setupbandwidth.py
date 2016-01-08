import os, sys, shlex
import subprocess

def createDir(direc):
	command = "mkdir "+direc
	#print "create dir for ", direc

	if not (os.path.exists(direc) and os.path.isdir(direc)):
		os.system(command) 
 
def runspeedtest():
 	sc = shlex.split("./speedtest-cli")
	#print "\nSpeedTest: "
	sc = subprocess.check_output(sc)
	#print sc
	return sc

def runping():
	pc = shlex.split("ping -c 10 www.google.com")
	#print '\n Ping to Google'
	pc = subprocess.check_output(pc)
	#print pc
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

upbandwidths = ['500kbit', '1mbit']
downbandwidths = ['2mbit', '5mbit', '10mbit']
upbandwidths = ['500', '1000']
downbandwidths = ['2000', '5000']
latencies = ['10ms','50ms']
burst = ['100000k', '1000000k', '1000000k']

interfacename = 'wlan0'

def clearallqdisc(interfacename):
	command = 'sudo tc qdisc del dev '+interfacename+' root'
	#print command
	os.system(command)
	command = 'sudo tc qdisc del dev '+interfacename+' ingress'
	#print command
	os.system(command)
	command = 'sudo tc qdisc del dev ifb0 root'
	#print command
	os.system(command)
	command = 'sudo tc qdisc del dev ifb0 root'
	#print command	
	os.system(command)

args = sys.argv
#print args
if 'stop' in args:
	if len(args) == 3:
		interfacename = args[2]
	clearallqdisc(interfacename)
	sys.exit(0)
elif len(args) == 3 or len(args) == 4:
	#clearallqdisc(interfacename)
	if len(args) == 4:
		interfacename = args[1]
		downbw = args[2]
		upbw = args[3]
	else:
		downbw = args[1]
		upbw = args[2]
	clearallqdisc(interfacename)
	print 'Configuring bandwidth...'
	os.system('sudo wondershaper '+interfacename+' '+downbw+' '+upbw)
	#sc = runspeedtest()
	#st = parsespeedtest(sc)
	#print 'Current speeds (using speedtest) are: download  %s, upload %s' %(st[1], st[0])
	#pc = runping()
	#pingres = parsepingoutput(pc)
	#print 'Current Latency to Google is %s' % (pingres)
	#os.system('python firefox/WebTester.py')
	print '...............................................................\n\n'
	sys.exit(0)
else:
	print 'Please enter "python setupbandwidth.py [interfacename] downloadspeed uploadspeed" (speed in kbps)'
	print 'OR enter "python setupbandwidth.py [interfacename] stop" to stop bandwidth configuration'

