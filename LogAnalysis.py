import sys,os,logging
from urlparse import urlparse

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

def createDependecyGraph(dirPath, prefix, hostSet):
	allFiles = os.listdir(dirPath)
	selectedFiles = set()
	for fname in allFiles:
		if fname.startswith(prefix):
			selectedFiles.add(fname)
	logger.debug("host set's size:%d"%len(hostSet))
	logger.debug("found %d traces for creating dependency graph"%len(curHostSet))	
	#records an url's parent
	parentGraph = {}

	buf = []
	
	for item in selectedFiles:
		f = open(os.path.join(dirPath,item))
		targetURL = None
		startChildrenReq = False
		childSet = set()
		noParentSet = set()
		potentialParentSet = set()
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
			if targetURL == None:
				if parts[1].startswith('TARGETURL') and parts[2].strip()=='START':
					targetURL = t
				else:
					potentialParentSet.add(t)
			else:
				if startChildrenReq:
					if (not t in potentialParentSet) and \
						(not t in noParentSet):
						childSet.add(t)
					else:
						logger.warning("%s appear as both children and non-children [%s]" %(t,targetURL))
				elif parts[1].startswith('TARGETURL') and parts[2].strip()=='END':
					startChildrenReq = True
				else:
					if not t in potentialParentSet:
						noParentSet.add(t)
		f.close()
		
		#remove targetURL's parent URLS that are in noParentSet
		if targetURL in parentGraph:
			for p in parentGraph[targetURL]:
				if p in noParentSet:
					logger.debug("Found parent:%s in noPanrentSet[%s]. Remove it" %(p,targetURL) )
					parentGraph[targetURL].remove(p)
		else:
			parentGraph[targetURL] = []

		#update childSet's parent
		for item in childSet:
			if not item in parentGraph:
				parentGraph[item] = []
			#detect loop and make sure item is not in TargetURL's parent list
			#remove TargetURL's parents from item's parent list
			

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

def main():
	hostSet = getCommonURLHostsFromDir(sys.argv[1],'www.cnn.com')
	f = open('cnnHostList','w')
	for line in hostSet:
		f.write(line+"\n")
	f.close()

if __name__ == '__main__':
	main()