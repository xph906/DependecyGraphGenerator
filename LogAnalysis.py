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
		f = open(item)
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

def main():
	hostSet = getCommonURLHostsFromDir(sys.argv[1],'www.cnn.com')
	f = open('cnnHostList','w')
	for line in hostSet:
		f.write(line+"\n")
	f.close()

if __name__ == '__main__':
	main()