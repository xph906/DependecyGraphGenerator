import sys,os,logging,pydot,json,re,argparse
from urlparse import urlparse
from Queue import Queue

logger = logging.getLogger('loganalysis.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)

def getCommonURLHostsFromDir(dirPath, prefix):
	allFiles = os.listdir(dirPath)
	selectedFiles = set()
	for fname in allFiles:
		if fname.startswith(prefix):
			selectedFiles.add(fname)
	
	sets = []
	curHostSet = set()
	for item in selectedFiles:
		curHostSet = set()
		f = open(os.path.join(dirPath,item))
		for line in f:
			parts = line.strip().split()
			if len(parts)==3 and parts[1].startswith('REGULARURL'):
				try:
					index = parts[1].find(':')
					url = parts[1][index+1:]
					o = urlparse(url)
					t = "%s://%s%s" %(o.scheme, o.netloc, o.path)
					curHostSet.add(t)
				except Exception as e:
					logger.warning("no url found in "+parts[1])
		if len(curHostSet) > 10:
			logger.debug("length of distinct hosts: %d"%len(curHostSet))
			sets.append(curHostSet)
		else:
			logger.debug("get rid of this host set for its length: %d"%len(curHostSet))
		f.close()
	if len(sets) == 0:
		return None
	curHostSet = sets[0]
	for s in sets:
		curHostSet &= s

	#for s in sets:
	#	for item in s:
	#		if not item in curHostSet:
	#			logger.debug("unique host:"+item)
	logger.debug("common set's length: %d"%len(curHostSet))
	logger.debug(curHostSet)
	return curHostSet

def createDependecyGraph(dirPath, firstURL,prefix, hostSet):
	allFiles = os.listdir(dirPath)
	selectedFiles = set()
	for fname in allFiles:
		if fname.startswith(prefix):
			selectedFiles.add(fname)
	logger.debug("host set's size:%d"%len(hostSet))
	logger.debug("found %d traces for creating dependency graph"%len(hostSet))	
	#records an url's parent
	parentGraph = {}
	if not firstURL in hostSet:
		logger.error("first url %s is not in hostSet"%firstURL)
		return None,None,None
	for item in hostSet:
		if item != firstURL:
			parentGraph[item] = [firstURL]
		else:
			parentGraph[item] = []

	################Logfile Organization#############	
	# Begin											#
	# ... 					potentialParentSet		#
	# TargetURL Start 								#
	# ... 					noParentSet 			#
	# TargetURL End 								#
	# ... 					childSet				#
	# End 											#
	#################################################
	badLogs = []
	for fileName in selectedFiles:
		f = open(os.path.join(dirPath,fileName))
		targetURL = None
		startChildrenReq = False
		childSet = set()
		noParentSet = set()
		potentialParentSet = set()
		ignoreSet = set()

		logger.debug("\nstart processing file:%s"%fileName)
		for line in f:
			parts = line.strip().split()
			if len(parts) != 3:
				continue
			try:
				index = parts[1].find(':')
				url = simplifyURL(parts[1][index+1:])
				o = urlparse(url)
				t = "%s://%s%s" %(o.scheme, o.netloc, o.path)
			except Exception as e:
				logger.warning("no url found in "+parts[1])
				continue
			if not t in hostSet:
				ignoreSet.add(url)
				continue
			# Add urls to different lists
			if targetURL == None:
				if parts[1].startswith('TARGETURL') and parts[2].strip()=='START':
					targetURL = t
					logger.debug("target url: "+t)
				else:
					potentialParentSet.add(t)
			else:
				if startChildrenReq:
					childSet.add(t)
				elif parts[1].startswith('TARGETURL') and parts[2].strip()=='END':
					startChildrenReq = True
				else:
					noParentSet.add(t)
		f.close()
		if targetURL == None:
			badLogs.append(fileName)
			logger.error("File "+fileName+" is bad")
		#further modify each set to ensure an url appear in at most one set
		removeList = []
		for item in noParentSet:
			if item in potentialParentSet:
				removeList.append(item)
		for item in removeList:
			noParentSet.remove(item)
		logger.warning("remove %d urls from noParentSet"%len(removeList))

		removeList = []
		for item in childSet:
			if item in potentialParentSet or \
				item in noParentSet:
				removeList.append(item)
		for item in removeList:
			childSet.remove(item)
		logger.warning("remove %d urls from childSet"%len(removeList))			

		logger.debug("done processing file:%s with [c:%d] [np:%d] [pp:%d] [ignore:%d] " \
						%(fileName,len(childSet),len(noParentSet),len(potentialParentSet),len(ignoreSet) ))
		
		#remove targetURL's parent URLS that are in noParentSet
		removeList = []
		if targetURL in parentGraph:
			for p in parentGraph[targetURL]:
				if p in noParentSet:
					removeList.append(p)
			for item in removeList:
				parentGraph[targetURL].remove(item)
			logger.warning("remove %d urls from targetURL's parents"%len(removeList))
		else:
			parentGraph[targetURL] = []

		#update childSet's parent
		logger.debug("Start updating childSet's parents")
		grandParents = getAllSuccessor(parentGraph,targetURL)
		for item in childSet:
			if parentGraph[item] == None:
				logger.warning("Only firstURL's parentList is None, this one is: %s"%item)
				continue
			if item == targetURL:
				continue
			if targetURL in parentGraph[item]:
				continue
			#detect loop and make sure item is not in TargetURL's parent list
			if item in grandParents:
				logger.debug("%s is already %s parent. don't make it as children" %(item,targetURL) )
				continue
			#remove TargetURL's parents from item's parent list
			for gp in grandParents:
				if gp in parentGraph[item]:
					parentGraph[item].remove(gp)
			parentGraph[item].append(targetURL)			
	
	childGraph = {}
	for child in parentGraph:
		if not child in childGraph:
			childGraph[child] = []
		for parent in parentGraph[child]:
			if not parent in childGraph:
				childGraph[parent] = [child]
			else:
				childGraph[parent].append(child)

	return parentGraph,childGraph,badLogs

def DrawFigure(graph,head):
	#degree = 0
	queue = Queue()
	queue.put(head)
	visitedSet = set()
	g = pydot.Dot(graph_type='digraph')
	while not queue.empty():
		item = queue.get()
		if item in visitedSet:
			continue
		nodeParent = pydot.Node(tagURL(item), style="filled", fillcolor="green")
		for succ in graph[item]:
			nodeChild = pydot.Node(tagURL(succ), style="filled", fillcolor="green")
			g.add_edge(pydot.Edge(nodeParent, nodeChild))
			queue.put(succ)
		visitedSet.add(item)
	g.write_png('example2_graph.png')

def LongestPath(parentGraph,node,path,degree=0):
	path.append(node)
	if len(parentGraph[node]) == 0:
		print path[0],str(len(path)),":"
		for m in reversed(path):
			print tagURL(m),'->',
		print '\n'
		return degree,path

	maxDegree = degree
	longestPath = []
	for p in parentGraph[node]:
		tmpDegree,tmpPath = LongestPath(parentGraph,p,path[:],degree+1)
		if tmpDegree > maxDegree:
			maxDegree = tmpDegree
			longestPath = tmpPath

	return maxDegree, longestPath
	
def getAllSuccessor(graph,node):
	resultSet = set()
	queue = Queue()
	for item in graph[node]:
		#print item
		queue.put(item)
	
	while not queue.empty():
		item = queue.get()
		if item in resultSet:
			continue
		resultSet.add(item)
		#if graph[item] == None:
		#	continue
		for n in graph[item]:
			if not n in resultSet:
				queue.put(n)
	
	return resultSet

def simplifyURL(url):
	tmps = url.split('/')
	for i in range(len(tmps)):
		m = re.match("[\d\.]+$",tmps[i])
		if m != None:
			tmps[i] = "number%d" %len(tmps[i])	
	return '/'.join(tmps) 

#all hosts have to be lowercase	
#1.111.1 will be replaced with 'number7'
def readHostList(filePath):
	f = open(filePath)
	data = []
	for line in f:
		line = line.strip().lower()
		data.append(simplifyURL(line))
	return data	

def tagURL(url):
	o = urlparse(url)
	rs = None
	tmp = o.netloc
	if tmp.startswith('www.'):
		tmp = o.netloc[4:]
	
	rs = tmp+'/'
	if len(o.path) > 10:
		 rs += '...'+o.path[len(o.path)-8:]
	elif o.path == '/':
		pass
	else:
		rs += o.path
	return rs

#def analyzeBroLogWithMultipleInstances(filePath,firstURL,endURL):
#	for line in f:

#firstURL/endURL scheme+"://"+netloc+path	
def analyzeBroLogWithMultipleEndURLs(filePath,firstURL,endURLSet):
	dnsTable = {} 			#host => ip
	handshakeTable = {} 	#ip => [conn time]
	objectSizeTable = {}	#scheme+"://"+netloc+path => [obj size]
	intervalRusults = []
	transmittionTime = {}
	firstURLTime = 0
	endURLTimeSet = {}
	for item in endURLSet:
		endURLTimeSet[item] = 0

	f = open(filePath)
	for line in f:
		line = line.strip().lower()
		try:
			item = json.loads(line)
		except Exception as e:
			logger.error("failed to parse %s as json object "%line)
			continue
		if item['tag'] == "conne":
			ip = item['dstip'].strip()
			if not ip in handshakeTable:
				handshakeTable[ip] = []
			handshakeTable[ip].append(item['duration'])
		elif item['tag'] == "req":
			ip = item['dstip'].strip()
			url = simplifyURL(item['url'].strip())
			o = urlparse(url)
			shortURL = o.scheme+"://"+o.netloc+o.path
			host = o.scheme+'://'+o.netloc
			if not host in dnsTable:
				dnsTable[host] = ip
			if firstURL == shortURL:
				firstURLTime = item['time']
			elif shortURL in endURLSet:
				if endURLTimeSet[shortURL] != 0:
					continue
				endURLTimeSet[shortURL] = item['time']
				done = True
				for t in endURLTimeSet:
					if endURLTimeSet[t] == 0:
						done = False
						break	
				if done:
					interval = item['time'] - firstURLTime
					intervalRusults.append(interval)
					for item in endURLTimeSet:
						interval = endURLTimeSet[item] - firstURLTime
						#logger.debug("[lasturl:%s] interval of %s object: %f"%(shortURL,item,interval) )
						endURLTimeSet[item] = 0 
					firstURLTime = 0
							
		elif item['tag'] == "respd":
			url = simplifyURL(item['url'].strip())
			o = urlparse(url)
			shortURL = o.scheme+"://"+o.netloc+o.path
			if not shortURL in objectSizeTable:
				objectSizeTable[shortURL] = []
			objectSizeTable[shortURL].append(item['size'])
	
			url = item['url'].strip()
			if url in transmittionTime:
				first = transmittionTime[url][0] 
				transmittionTime[url] = (first,item['time'])
		elif item['tag'] == "respb":
			url = item['url'].strip()
			transmittionTime[url] = (item['time'],0)
	
	transmittionTime2 = {}
	for url in transmittionTime:
		duration = str(transmittionTime[url][1] - transmittionTime[url][0])
		sURL = simplifyURL(url)
		o = urlparse(sURL)
		sURL = o.scheme+"://"+o.netloc+o.path
		if not sURL in transmittionTime2:
			transmittionTime2[sURL] = [duration]
		else:
			transmittionTime2[sURL].append(duration)
	
	return dnsTable,handshakeTable,objectSizeTable,intervalRusults,transmittionTime2


#firstURL/endURL scheme+"://"+netloc+path	
def analyzeBroLog(filePath,firstURL,endURL):
	dnsTable = {} 			#host => ip
	handshakeTable = {} 	#ip => [conn time]
	objectSizeTable = {}	#scheme+"://"+netloc+path => [obj size]
	intervalRusults = []
	transmittionTime = {}
	firstURLTime = 0
	#endURLTime = 0

	f = open(filePath)
	for line in f:
		line = line.strip().lower()
		try:
			item = json.loads(line)
		except Exception as e:
			logger.error("failed to parse %s as json object "%line)
			continue
		if item['tag'] == "conne":
			ip = item['dstip'].strip()
			if not ip in handshakeTable:
				handshakeTable[ip] = []
			handshakeTable[ip].append(item['duration'])
		elif item['tag'] == "req":
			ip = item['dstip'].strip()
			url = simplifyURL(item['url'].strip())
			o = urlparse(url)
			shortURL = o.scheme+"://"+o.netloc+o.path
			host = o.scheme+'://'+o.netloc
			if not host in dnsTable:
				dnsTable[host] = ip
			if firstURL == shortURL:
				firstURLTime = item['time']
			elif endURL == shortURL:
				if firstURLTime != 0:
					interval = item['time'] - firstURLTime
					logger.warning("one brosing instance")
					intervalRusults.append(interval)
					firstURLTime = 0
				else:
					logger.warning("firstURLTime is 0 while endURLtime is not!")
		elif item['tag'] == "respd":
			url = simplifyURL(item['url'].strip())
			o = urlparse(url)
			shortURL = o.scheme+"://"+o.netloc+o.path
			if not shortURL in objectSizeTable:
				objectSizeTable[shortURL] = []
			objectSizeTable[shortURL].append(item['size'])
	
			url = item['url'].strip()
			if url in transmittionTime:
				first = transmittionTime[url][0] 
				transmittionTime[url] = (first,item['time'])
		elif item['tag'] == "respb":
			url = item['url'].strip()
			transmittionTime[url] = (item['time'],0)
	
	transmittionTime2 = {}
	for url in transmittionTime:
		duration = str(transmittionTime[url][1] - transmittionTime[url][0])
		sURL = simplifyURL(url)
		o = urlparse(sURL)
		sURL = o.scheme+"://"+o.netloc+o.path
		if not sURL in transmittionTime2:
			transmittionTime2[sURL] = [duration]
		else:
			transmittionTime2[sURL].append(duration)
	
	return dnsTable,handshakeTable,objectSizeTable,intervalRusults,transmittionTime2

def loadGraphMapFromFile(path):
	fin = open(path)
	graph = {}
	for line in fin:
		line = line.strip()
		item = json.loads(line)
		graph[item['node']] = item['parents']
	return graph

def getIPFromURL(url,dnsTable):
	o = urlparse(url)
	k = o.scheme+"://"+o.netloc
	if k in dnsTable:
		return dnsTable[k]
	else:
		return None

def parse_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('--function','-f', help='the function to execute')
	parser.add_argument('--prefix','-p', help='prefix of file names')
	parser.add_argument('--dir','-d', help='directory of log files')
	parser.add_argument('--firsturl','-fu', help='the first url of each trace')
	parser.add_argument('--lasturl','-lu', help='the last url of each trace')
	parser.add_argument('--finalurls','-lus', help='the path of file containing essential urls')
	parser.add_argument('--commonurllist','-c', help='the path of valid object url list')
	parser.add_argument('--graphoutputpath','-go', help='the path to output the graph')
	parser.add_argument('--hostlistoutpath','-ho', help='the path to output the common host list')
	parser.add_argument('--graphinputpath','-gi', help='the path of graph to read from')
	parser.add_argument('--brofilepath','-b', help='the path of bro log')
	args = parser.parse_args()
    
	return args


def main():
	args = parse_arguments()
	if args.function == "getcommonurl":
		#Extract Common Hosts
		#'''
		hostSet = getCommonURLHostsFromDir(args.dir,args.prefix)
		f = open(args.hostlistoutpath,'w')
		for line in hostSet:
			f.write(line+"\n")
		f.close()
		#'''
	elif args.function == "generategraph":
		#Generate Graph
		#createDependecyGraph(dirPath, firstURL,prefix, hostSet)
		#argv[1]: dirPath
		#argv[2]: firstURL
		#argv[3]: prefix
		#argv[4]: hostPath
		#argv[5]: graph output path
		hostSet = readHostList(args.commonurllist)
		fout = open(args.graphoutputpath,'w')
		graph,childGraph,badLogs = createDependecyGraph(args.dir,args.firsturl,args.prefix, hostSet)
		#graph = pydot.Dot(graph_type='graph')
		#DrawFigure(childGraph,sys.argv[2])
		degreeGraph = {}
		for item in hostSet:
			l,p = LongestPath(graph,item,[],0)
			degreeGraph[item] = (l,p)

		degreeList = sorted(degreeGraph.items(), key=lambda x: x[1][0], reverse=True)
		for item in degreeList:
			print "[%2d] %s"%(item[1][0],item[0])
		
		for badLog in badLogs:
			print "badLog: ",badLog	
		
		#s = getAllSuccessor(graph,hostSet[20])
		#print "%s's parents:" % hostSet[20]
		#for item in s:
		#	print '  ',item
		#print ""

		jsonItemFormatter = '{"node":"%s","parents":%s}'
		for item in graph:
			jsonItem = jsonItemFormatter%(item,json.dumps(graph[item]))
			fout.write(jsonItem+'\n')
		fout.close()
		
		#graph = loadGraphMapFromFile(sys.argv[1])
		#hostSet = readHostList(sys.argv[2])
		#s = getAllSuccessor(graph,hostSet[20])
		#print "%s's parents:" % hostSet[20]
		#for item in s:
		#	print '  ',item
		#print ""
		
	elif args.function == "analyzebrolog":	
		#parse Bro logs
		# argv[1]: broFilePath
		# argv[2]: firstURL
		# argv[3]: graphPath
		# argv[4]: hostPath
		graph = loadGraphMapFromFile(args.graphinputpath)
		hostSet = readHostList(args.commonurllist)
		#finalURL = "http://cdn.krxd.net/controltag"
		if args.lasturl:
			finalURL = args.lasturl
			parents = getAllSuccessor(graph,finalURL)
			logger.debug("length of parents: %d" % len(parents))
			dnsTable,handshakeTable,sizeTable,intervalRusults,transmittionTable = \
							analyzeBroLog(args.brofilepath,args.firsturl,finalURL)
		else:
			tmp = readHostList(args.finalurls)
			finalURLSet = set()
			for item in tmp:
				if item in hostSet:
					finalURLSet.add(item)
			parents = set()
			parents = parents | finalURLSet
			for item in finalURLSet:
				curParent = getAllSuccessor(graph,item)
				parents = curParent | parents
			logger.debug("length of finalurls:%d and parents: %d" % (len(finalURLSet),len(parents)))
			dnsTable,handshakeTable,sizeTable,intervalRusults,transmittionTable = \
				analyzeBroLogWithMultipleEndURLs(args.brofilepath,args.firsturl,finalURLSet)
		#parents = set()
		#analyzeBroLog(filePath,firstURL,endURL)
		
		tmpDict = {}
		
		for p in parents:
			o = urlparse(p)
			k = o.scheme+"://"+o.netloc+o.path
			if not k in tmpDict:
				ip = getIPFromURL(p,dnsTable)
				if ip == None:
					print "can't find %s's IP" % p
					continue
				total = 0
				for t in handshakeTable[ip]:
					total += t
				avgTime = total/len(handshakeTable[ip])

				total = 0
				if not k in sizeTable:
					print "can't find url %s from sizeTable" %k
					continue
				for t in sizeTable[k]:
					total += t
				totalSize = total
				
				if not k in transmittionTable:
					print "can't find url %s from transmittionTable" %k
					continue
				
				tt = "[" + '|'.join(transmittionTable[k]) +"]"
				tmpDict[k] = (1,avgTime,len(handshakeTable[ip]),totalSize,len(sizeTable[k]),tt)
				
			else:
				x = tmpDict[k]
				tmpDict[k] = (x[0]+1,x[1],x[2],x[3],x[4],x[5])
		
		for item in tmpDict:
			print item,":",str(tmpDict[item])
			
		print "inteval results: ",
		for item in intervalRusults:
			print str(item),
		

if __name__ == '__main__':
	main()
