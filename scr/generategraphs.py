__author__ = 'Dipendra'
import sys, os
sys.path.append('/Users/Dipendra/Libs/')
from pialab import graph, utils as myutils
resultfolder = os.path.join(os.getcwd(),'resultsnormal')
results = {}
for fil in os.listdir(resultfolder):
		#try:
		site = None
		purl = None
		delay = None
		loadtime = None
		if not os.path.isfile(os.path.join(resultfolder,fil)):
			continue
		data = open(os.path.join(resultfolder,fil)).read().strip()
		print '\n\n',fil
		print data
		if not 'User' in data:
			continue
		data = data.split('\n')
		firstline = data[0].replace('UserPerceived:','')
		print 'firstline:', firstline
		if firstline != 'None':
			if data[1] != 'None' and len(eval(data[1])) != 0:
				#print data
				firstline = data[0].replace('UserPerceived:','')
				purl = eval(firstline)[1].strip()
				#print purl
				print data[1]
				print data[1][0]
				delay = [ x.replace('STARTTIME:','').replace('ENDTIME:','').replace(']','').replace('[','') for x in eval(data[1])[0].split('][') if 'TIME' in x]
				print data[1][0]
				print delay
				delay = float(delay[1]) - float(delay[0])
			else:
				delay = float(eval(firstline)[-1].strip())
				#print delay
			sdata = data[2].split('\t')
			#print sdata
			site = sdata[0]
			loadtime = float(sdata[3])
				
		else:
			#continue
			site = data[2].split('\t')[0]
			loadtime = float(data[2].split('\t')[-1])
			delay = loadtime
			purl = site
		if not results.has_key(site):
			results[site] = {}
			results[site]['finalurl'] = set()
			results[site]['updelay'] = []
			results[site]['pageloadtime'] = []
		results[site]['finalurl'].add(purl)
		if delay <= loadtime:
			results[site]['updelay'].append(delay)
			results[site]['pageloadtime'].append(loadtime)
		else:
			results[site]['updelay'].append(loadtime)
			results[site]['pageloadtime'].append(loadtime)
		print '\nResults::::site:', site,' finalurl:',str(purl),' delay:',str(delay), ' loadtime:',str(loadtime)
		#except:
		pass


print len(results.keys())
print results.keys()
graphdata = {}
percenttime = []
for (site, data) in results.iteritems():
	ptimes = data['pageloadtime']
	ptime = sum(ptimes)/len(ptimes)
	results[site]['pageloadtime'] = ptime
	dtimes = data['updelay']
	dtime = sum(dtimes)/len(dtimes)
	results[site]['updelay'] = dtime
	finalurl = data['finalurl']
	#if dtime > ptime:
	#	print site, dtimes, ptimes
	print site, dtime, ptime
	graphdata[ptime] = dtime
	percenttime.append(100*float(dtime)/ptime)

pdata = sorted(graphdata.keys())
ddata = [graphdata[x] for x in pdata]

graphdata = [ddata, pdata]

graph.linegraph('Line graph of UPD and FPLT(new)','Number of websites','Time in Seconds', ['User Perceived Delay', 'Full Page Load Time'],range(1,len(graphdata[0])+1),graphdata, os.getcwd(), legendposition='upper left')
graph.plotcdf(graphdata,['User Perceived Delay','Full Page Load Time'],'CDF of UPD and FPLT(new) ',os.getcwd(),'Time in seconds')
graph.plotcdf([percenttime],['Percentage UPD to FPLT'],'CDF of UPD and FPLT (percentage)(new) ',os.getcwd(),'UPD as percentage of FPLT')

