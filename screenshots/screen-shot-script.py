import sys
import os
from libmproxy.flow import FlowWriter
from libmproxy.protocol.http import decoded
from PIL import Image as pimg
import pyscreenshot as ImageGrab

f = open("output.log", "w+")

def start(context, flow):
	f.truncate()

def request(context, flow):
	time.sleep(5)

#just print out the lengths of each response for now
def response(context, flow):
	# fullscreen
	im = ImageGrab.grab()
	im.save("outputImage.png", "PNG")

	size = os.path.getsize("outputImage.png")

	f.write(str(flow.request.host) + " " + str(size) + '\n')

def done(context):
	f.close()
	os.remove("outputImage.png")
