import sys, time, os, threading
from libmproxy.flow import FlowWriter
from libmproxy.protocol.http import decoded
from libmproxy.script import concurrent
from PIL import Image as pimg
import Image
import pyscreenshot as ImageGrab
from urlparse import urlparse
import shutil
import socket

pre_pic = ImageGrab.grab()
post_pic = ImageGrab.grab()

def start(context, flow):
	context.lock = threading.RLock()	
	context.lastTime = 0
	context.stop_analysis = False
	pre_pic = ImageGrab.grab();
	pre_pic.save("outputImagePre.png", "PNG")
	open("output.log", "w").close()
	

##we want each request to be 5 seconds apart from *each other*
@concurrent
def request(context, flow):

	## locking...
	context.lock.acquire()

	## critical section - set your current waitTime and next lastTime
        waitTime = context.lastTime + 5
	context.lastTime += 5

	## releasing lock
	context.lock.release()

        time.sleep(waitTime)	

#just print out the lengths of each response for now
def response(context, flow):

	# fullscreen screenshot, save it locally for now
	post_pic = ImageGrab.grab()
	post_pic.save("outputImagePost.png", "PNG")

       	url = "%s://%s%s" % (flow.request.scheme,flow.request.host,flow.request.path)
       	o = urlparse(url)
       	url = "%s://%s%s" % (flow.request.scheme,o.netloc,o.path)
       	url = url.lower()
		
	f = open("output.log", "a")

	picture_similar = calc_similar_by_path("outputImagePre.png", "outputImagePost.png")
	info = '[SIMILAR:%f][REQUEST:%s]' % (picture_similar, str(url))

	f.write(info + '\n')

	if picture_similar <= 0.85 and picture_similar > 0.75:
		f.write("FOUND THRESHOLD HERE\n")

	shutil.copy("outputImagePost.png", "outputImagePre.png")

	if picture_similar <= 0.85 and picture_similar > 0.75:
		f.write("SENDING MESSAGE TO LOCALHOST 9090\n")
		clientsocket = socket.socket(socket.AF_INET, socket.OSCK_STREAM)
		clientsocket.connect(('localhost', 9090))
		clientsocket.sendall("done")

	f.close()

def make_regalur_image(img, size = (256, 256)):
    return img.resize(size).convert('RGB')

def split_image(img, part_size = (64, 64)):
	w, h = img.size
	pw, ph = part_size
	assert w % pw == h % ph == 0
	return [img.crop((i, j, i+pw, j+ph)).copy() \
                for i in xrange(0, w, pw) \
                for j in xrange(0, h, ph)]

def hist_similar(lh, rh):
	assert len(lh) == len(rh)
	return sum(1 - (0 if l == r else float(abs(l - r))/max(l, r)) for l, r in zip(lh, rh))/len(lh)

def calc_similar(li, ri):
	return sum(hist_similar(l.histogram(), r.histogram()) for l, r in zip(split_image(li), split_image(ri))) / 16.0

def calc_similar_by_path(lf, rf):
	li, ri = make_regalur_image(Image.open(lf)), make_regalur_image(Image.open(rf))
	return calc_similar(li, ri)

