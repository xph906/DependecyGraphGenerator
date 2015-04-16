import sys,os,logging,pydot
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
		if len(curHostSet) > 100:
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
		return None
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
				url = parts[1][index+1:]
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
		nodeParent = pydot.Node(simplifyURL(item), style="filled", fillcolor="green")
		for succ in graph[item]:
			nodeChild = pydot.Node(simplifyURL(succ), style="filled", fillcolor="green")
			g.add_edge(pydot.Edge(nodeParent, nodeChild))
			queue.put(succ)
		visitedSet.add(item)
	g.write_png('example2_graph.png')

def LongestPath(parentGraph,node,path,degree=0):
	path.append(node)
	if len(parentGraph[node]) == 0:
		print path[0],str(len(path)),":"
		for m in reversed(path):
			print simplifyURL(m),'->',
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
		queue.put(item)
	
	while not queue.empty():
		item in queue.get()
		if item in resultSet:
			continue
		resultSet.add(item)
		#if graph[item] == None:
		#	continue
		for n in graph[item]:
			if not n in resultSet:
				queue.put(n)
	
	return resultSet

#all hosts have to be lowercase	
def readHostList(filePath):
	f = open(filePath)
	data = []
	for line in f:
		line = line.strip().lower()
		data.append(line)
	return data	

def simplifyURL(url):
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
	
def analyzeBroLog(filePath):
	dnsTable = {} #host => ip
	handshakeTable = {} #ip => [conn time]
	f = open(filePath)
	for line in f:
		line = line.strip().lower()
		item = json.loads(line)

def main():
	'''
	hostSet = getCommonURLHostsFromDir(sys.argv[1],'www.cnn.com')
	f = open('cnnHostList','w')
	for line in hostSet:
		f.write(line+"\n")
	f.close()
	'''
	#createDependecyGraph(dirPath, firstURL,prefix, hostSet)
	#argv[1]: dirPath
	#argv[2]: firstURL
	#argv[3]: prefix
	#argv[4]: hostPath
	hostSet = readHostList(sys.argv[4])
	graph,childGraph,badLogs = createDependecyGraph(sys.argv[1], sys.argv[2],sys.argv[3], hostSet)
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

			

if __name__ == '__main__':
	main()