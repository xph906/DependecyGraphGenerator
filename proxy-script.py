from libmproxy.protocol.http import HTTPResponse
from netlib.odict import ODictCaseless
from libmproxy.script import concurrent
import threading,os,time,argparse,sys


def start(context, argv):
    if len(argv) != 6:
        print >>sys.stderr, "argv length:",str(len(argv)),argv[len(argv)-2]
        raise ValueError('Usage: -s "script.py firstURL suspendURL LogDir logFile threshold"')
    context.root = argv[3]
    if (not os.path.exists(context.root)) or \
        (not os.path.isdir(context.root) ):
        raise ValueError("path %s doesn't exist"%(context.root) )
    context.threshold = int(argv[5])
    context.fullLogPath = os.path.join(context.root,argv[4]) 
    context.firstURL = argv[1].lower().strip()
    context.suspendURL = argv[2].lower().strip()
    if context.suspendURL == "none":
        context.suspendURL = None
    context.outFile = open(context.fullLogPath,'w')
    context.lock = threading.RLock()
    

@concurrent
def request(context, flow):
    if flow.request.pretty_host(hostheader=True).endswith("localhost"):
        if flow.request.path.strip().startswith("/commands/exit"):
            resp = HTTPResponse(
                [1, 1], 200, "OK",
                ODictCaseless([["Content-Type", "text/html"]]),
                "done %s"%context.fullLogPath)
            context.lock.acquire()
            context.outFile.write('EndFile\n')
            context.outFile.close()
            context.lock.release()
            print "close file ",context.fullLogPath
            flow.reply(resp)
        else:
            print flow.request.path.strip()
    
    url = "%s://%s%s" % (flow.request.scheme,flow.request.host,flow.request.path)
    currentTime = int(time.time())
    if url == context.firstURL:
        context.lock.acquire()
        print "find first url ",url
        context.startTime = currentTime
        context.lock.release()

    if context.suspendURL and (url == context.suspendURL):
        print "target url wait for %d seconds" % context.threshold
        context.lock.acquire()
        log="%d TARGETURL:%s START\n" % (currentTime,url)
        context.outFile.write(log)
        context.lock.release()
        time.sleep(context.threshold)
        currentTime = int(time.time())
        context.lock.acquire()
        log="%d TARGETURL:%s END\n" % (currentTime,url)
        context.outFile.write(log)
        context.lock.release()
    else:
        context.lock.acquire()
        log="%d REGULARURL:%s END\n" % (currentTime,url)
        context.outFile.write(log)
        context.lock.release()
    
    
    
    

    