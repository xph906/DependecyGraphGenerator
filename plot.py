import mlpy
import numpy as np
import matplotlib.pyplot as plt
import re
import string
import json
import collections

def graph_bandwidth_latency():
    latency = []
    bandwidth = []

    bandlatmap = bandwidth_map()

    for i in range(1,len(bandlatmap)+1):
        format_bandwidth = '%d kbps' % i
        bandwidth.append(format(format_bandwidth))
        latency.append(bandlatmap[i])
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ind = np.arange(len(bandlatmap))
    
    ax.plot(ind, latency, 'black')
    ax.set_xticks(ind)
    ax.set_xticklabels(bandwidth)
    
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(5)

    plt.xlabel("Bandwidth")
    plt.ylabel("Latency")
    plt.title("Latency vs Bandwidth")
    plt.savefig("bandwidth_vs_latency.jpg")
    plt.close()

def bandwidth_map():
    i = 1
    bandlatmap = dict()
    files = ['10kb_output.txt', '20kb_output.txt', '30kb_output.txt']
    
    for file in files:
        with open(file, 'r') as f:
            data  = list()
            group = dict()
            
            #for latency in re.findall('[[0-9.]*]', f.read()):
            #latency = string.strip(latency, '[]')
            #print latency
            #blmap[i] = latency

            x = json.load(f)
            bandlatmap[i] = x["latency"]
                
            i = i+1

    return bandlatmap



def graph_rtt_latency():
    latency = []
    rtt = []

    rttlatmap = rtt_map()

    rttlatmap = collections.OrderedDict(sorted(rttlatmap.items()))
    
    for key, value in rttlatmap.iteritems():
        latency.append(value)
        rtt.append(key)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    #ind = np.arange(len(rttlatmap))
    
    ax.plot(rtt, latency, 'black')
    ax.set_xticks(rtt)
    ax.set_xticklabels(rtt)
    
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(5)

    plt.xlabel("Rtt")
    plt.ylabel("Latency")
    plt.title("Latency vs Rtt")
    plt.savefig("rtt_vs_latency.jpg")
    plt.close()

def rtt_map():
    rttlatmap = dict()
    files = ['10kb_output.txt', '20kb_output.txt', '30kb_output.txt']
    
    for file in files:
        with open(file, 'r') as f:
            data  = list()
            group = dict()
            
            #for latency in re.findall('[[0-9.]*]', f.read()):
            #latency = string.strip(latency, '[]')
            #print latency
            #blmap[i] = latency

            x = json.load(f)
            rttlatmap[x["rtt"]] = x["latency"]
                
    return rttlatmap



def graph_size_latency():
    latency = []
    size = []

    sizelatmap = size_map()

    sizelatmap = collections.OrderedDict(sorted(sizelatmap.items()))
    
    for key, value in sizelatmap.iteritems():
        latency.append(value)
        size.append(key)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    #ind = np.arange(len(sizelatmap))
    
    ax.plot(size, latency, 'black')
    ax.set_xticks(size)
    ax.set_xticklabels(size)
    
    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(5)

    plt.xlabel("Size")
    plt.ylabel("Latency")
    plt.title("Latency vs Size")
    plt.savefig("size_vs_latency.jpg")
    plt.close()

def size_map():
    sizelatmap = dict()
    files = ['10kb_output.txt', '20kb_output.txt', '30kb_output.txt']
    
    for file in files:
        with open(file, 'r') as f:
            data  = list()
            group = dict()
            
            #for latency in re.findall('[[0-9.]*]', f.read()):
            #latency = string.strip(latency, '[]')
            #print latency
            #blmap[i] = latency

            x = json.load(f)
            sizelatmap[x["size"]] = x["latency"]
                
    return sizelatmap

    
if __name__ == '__main__':
    graph_bandwidth_latency()
    graph_rtt_latency()
    graph_size_latency()
