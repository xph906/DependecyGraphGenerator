import os, sys, shlex
import subprocess

def createDir(direc):
	command = "mkdir "+direc
	#print "create dir for ", direc

	if not (os.path.exists(direc) and os.path.isdir(direc)):
		os.system(command) 
 
def runspeedtest():
 	sc = shlex.split("./speedtest-cli")
	print "\nSpeedTest: "
	sc = subprocess.check_output(sc)
	#print sc
	return sc

def runping():
	pc = shlex.split("ping -c 10 www.google.com")
	print '\n Ping to Google'
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

def clearallqdisc():
	command = 'sudo tc qdisc del wlan0 root'
	print command
	os.system(command)
	command = 'sudo tc qdisc del dev wlan0 ingress'
	print command
	os.system(command)
	command = 'sudo tc qdisc del dev ifb0 root'
	print command
	os.system(command)
	command = 'sudo tc qdisc del dev ifb0 root'
	print command	
	os.system(command)

def setupuploadspeed(upbw):
	command = 'sudo tc qdisc add dev wlan0 root handle 1: tbf rate '+upbw+' latency 50ms burst 1540'
	print command
	os.system(command)

def setupdownloadspeed(downbw):
	command = 'sudo modprobe ifb'
	print command
	os.system(command)
	command = 'sudo ip link set dev ifb0 down'
	print command
	os.system(command)
	clearallqdisc()
	command = 'sudo ip link set dev ifb0 up'
	print command
	os.system(command)
	'''	
	command p u32 match = 'sudo tc qdisc add dev ifb0 root handle 3: htb default 30'
	print command
	os.system(command)
	command = 'sudo tc class add dev ifb0 parent 3: classid 3:3 htb rate '+downbw
	print command
	os.system(command)
	command = 'sudo tc class add dev ifb0 parent 3:3 classid 3:30 htb rate '+downbw
	print command
	os.system(command)
	command = 'sudo tc class add dev ifb0 parent 3:3 classid 3:33 htb rate '+downbw
	print command
	os.system(command)
	command = 'sudo tc filter add dev ifb0 parent 3:0 protocol ip handle 3 fw flowid 3:33'
	print command
	os.system(command)
	'''
	command = 'sudo tc filter add dev wlan0 parent ffff: protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev ifb0'
	print command
	os.system(command)
	command = 'sudo tc qdisc add dev ifb0 root netem delay 10ms'
	print command
	os.system(command)
	return
	command = 'sudo tc qdisc add dev wlan0 ingress handle ffff:'
	print command
	os.system(command)
	#command = 'sudo tc filter add dev wlan0 parent ffff: protocol ip u32 match ip */* action mirred egress redirect dev ifb0 flowid ffff:1'
	command = 'sudo tc qdisc add dev ifb0 ingress handle 1: bandwidth '+downbw+ ' latency 50ms burst 1540'	
	print command
	os.system(command)
	


def setupdelay(delay):
	command = 'sudo modprobe ifb'
	print command
	os.system(command)
	command = 'sudo ip link set dev ifb0 up'
	print command
	os.system(command)
	command = 'sudo tc qdisc add dev ifb0 root netem delay '+delay	
	print command
	os.system(command)
	



while True:
	for downbw in downbandwidths:
		for u in range(len(upbandwidths)):
			upbw = upbandwidths[u]
			burstsize = burst[u]			
			'''				
			delcomm = 'sudo tc qdisc del dev wlan0 root'
			
			print '\ndeleting root qdisc:'
			print '\n',delcomm
			os.system(delcomm)			
			delcomm = 'sudo tc qdisc del dev wlan0 ingress'
			print '\n',delcomm
			os.system(delcomm)			
			setupdownloadspeed(downbw)
			setupuploadspeed(upbw)			
			'''
			os.system('sudo wondershaper wlan0 '+downbw+' '+upbw+' 30ms')			
			'''			
			addingress = 'sudo tc qdisc add dev wlan0 handle ffff: ingress'
			print '\n',addingress
			os.system(addingress)			
			bwcomm = 'sudo tc qdisc add dev wlan0 root handle 1:0 tbf rate '+upbw+' burst '+ burstsize + ' limit 1000000'
			print '\n',bwcomm			
			os.system(bwcomm)
			bwcomm = 'sudo tc qdisc add dev wlan0 ingress handle 1:1 cbf '+downbw
			print '\n',bwcomm			
			os.system(bwcomm)
			'''			
			'''			
			com1 = 'sudo tc qdisc add dev wlan0 root handle 1:1 htb default 30'
			print com1
			os.system(com1)
			com2 = 'sudo tc class add dev wlan0 parent 1: classid 1:1 htb rate '+downbw
			print com2
			os.system(com2)
			com3 = 'sudo tc class add dev wlan0 parent 1: classid 1:2 htb rate '+upbw
			print com3
			os.system(com3)
			com4 = 'sudo tc filter add dev wlan0 protocol ip parent 1:0 prio 1 u32 match ip dst 10.0.0.11/32 flowid 1:1'
			print com4
			os.system(com4)
			com5 = 'sudo tc filter add dev wlan0 protocol ip parent 1:0 prio 1 u32 match ip src 10.0.0.11/32 flowid 1:2'
			print com5
			os.system(com5)
			'''
			
			for lat in latencies:
				#labcomm = 'sudo tc qdisc replace dev wlan0 root handle 1: tbf delay '+ lat
				#print labcomm				
				#os.system(labcomm)
				#setupdelay(lat)
				command = 'sudo /sbin/tc qdisc add dev wlan0 handle 1: netem delay '+lat
				print command
				os.system(command)				
				sc = runspeedtest()
				st = parsespeedtest(sc)
				print 'Current speeds are: download  %s, upload %s' %(st[1], st[0])
				pc = runping()
				pingres = parsepingoutput(pc)
				print 'Current Latency to Google is %s' % (pingres)
				#os.system('python firefox/WebTester.py')
				print '...............................................................\n\n'
