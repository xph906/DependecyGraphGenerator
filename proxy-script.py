from libmproxy.protocol.http import HTTPResponse
from netlib.odict import ODictCaseless
from libmproxy.script import concurrent
import threading,os,time


def start(context, argv):
    if len(argv) != 4:
        raise ValueError('Usage: -s "script.py firstURL suspendURL logFile"')
    #remember to change root direcoty
    if '/' in argv[3]:
        raise ValueError('filename should not contain path info')
    
    #Configure
    context.root = "/Users/a/Projects/android/adsdisplay/mitmproxy_logs/"
    context.threshold = 10
    
    context.fullLogPath = os.path.join(context.root,argv[3]) 
    context.firstURL = argv[1].lower().strip()
    context.suspendURL = argv[2].lower().strip()
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

    if url == context.suspendURL:
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
    
    
    
    

    
