import os, sys, shlex
import subprocess, time

def createDir(direc):
	command = "mkdir "+direc
	#print "create dir for ", direc

	if not (os.path.exists(direc) and os.path.isdir(direc)):
		os.system(command) 
 

topsites = open('Global.txt').read()
topsites = eval(topsites)
#print topsites.keys()
topsitelist = [topsites[str(x)] for x in range(1,51)]
#print topsitelist

#sys.exit(0)
thresholds = ['0..6', '0.4']
delays = [1, 2, 5]
upbandwidths = ['2000', '2000','2000']
downbandwidths = ['5000', '5000', '5000']



def command(args, timeout=300):
	args = shlex.split(args)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	timeout = timeout/10
	op = ""
	if timeout == 0:
		timeout = 1
	time.sleep(5)
	for i in range(timeout):
		if p.poll() is 0:
			op, err = p.communicate(None)
			return op
		else:
			time.sleep(5)
	if p.poll() is not 0:
		p.kill()
		print 'Timeout, killed process'
	else:
		op, err = p.communicate(None)
	return op


def closeserver():
	try:
		print 'running command'
		output = command('sudo lsof -i :9090')
		#print output
		#output = open('test','r').read().split('\n')
		print output
		for lin in output:
			if not '9090' in lin:
				continue
			pid = lin.split(' ')
			pid = [x for x in pid if x != ''][1]
			os.system('sudo kill -9 '+pid)
	except:
		pass



while True:
	for downbw in downbandwidths:
		for upbw in upbandwidths:
			setdb = None
			setub = None
			bcommand = 'sudo python setupbandwidth.py eth0 '+downbw+' '+upbw
			try:
				op = command(bcommand)
				print op
				if op != "":
					setdb = downbw
					setub = upbw
			except:
				pass 
			for site in topsitelist:
				debugfile = open('debug','a')
				debugstring = ""
				try:
					perccommand = 'sudo python screenshot-firefox-driver.py -u http://www.'+site+' -t 1 -c screenshot_configure -d ./logs/ -hi 0.8 -lo 0 -s 1'
					print 'Running:\n',perccommand
					debugstring += '\nRunning'+perccommand+'\n'
					closeserver()
					time.sleep(10)
					try:
						output = command(perccommand,600)
						#print output
						debugstring += output +'\n'
					except:
						print 'error in running user perceived delay command'
					pobject = "None"
					data = "None"
					fetchdata = "None"
					try:
						pobject = open('results/results.log').read().split('\t')
						ct = time.time()
						print 'Results:',pobject
						debugstring += 'Results:' + str(pobject)
						lastobj = pobject[1].strip()
						print lastobj
					except:
						print 'error in getting result for user perceived delay'
						pass
					totalcommand = 'sudo python screenshot-firefox-driver.py -u http://www.'+site+' -t 1 -c screenshot_configure -d ./logs/ -hi 0 -lo 0 -s 0'
					print 'Running:\n',totalcommand
					closeserver()
					time.sleep(10)
					try:	
						debugstring += '\nRunning: '+totalcommand
						output = command(totalcommand)
						debugstring += '\nResults:'+output
						#print output			
						filename = os.path.join(os.getcwd(),'logs')
						filename = os.path.join(filename,'www.'+site+'_0')
						data = open(filename).read().strip().split('\n')
						debugstring += '\nAll timings: '+str(data)
						data = [x for x in data if lastobj in x]
						print 'Time for last object:',
						print data
						debugstring += '\nTime for last object: '+ str(data)
					except:
						print 'error in loading full page'
					try:
						fetchdata = open('fetchingtime.txt', 'r').read().split('\n')[-1]
						print 'Total fetch time'
						print fetchdata				
						debugstring += '\nfetchtime:'+str(fetchdata)
					except:
						print 'error in getting full page load time'
					try:
						result = '\nUserPerceived:'+str(pobject)+'\n'+str(data)+'\n'+str(fetchdata)
						bwset = '\nDownload:'+str(setdb)+'\tUpload:'+str(setub)
						ct = str(time.time())
						f = open('results/'+ct+site+'_nocache','w')
						f.write(result+bwset)
						debugstring += '\nWritten to file:'+str(ct)+str(site)+'\tresults:'+str(result)+str(bwset)
						f.close()
					except:
						pass
				except:
					continue

				debugfile.write(debugstring)
				debugfile.close()

