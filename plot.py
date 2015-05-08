import numpy as np
import matplotlib.pyplot as plt
import re
import string

def graph_latency():
    latency = []
    bandwidth = []

    #latency.append(32.1125798225)
    #latency.append(30.020966053)
    #latency.append(1.10881400108)
    #latency.append(1.11384797096)
    #latency.append(0.0633151531219)
    #latency.append(0.0560400485992)
    #latency.append(0.0553579330444)
    
    #bandwidth.append('100kbps')
    #bandwidth.append('500kbps')
    #bandwidth.append('750kbps')
    #bandwidth.append('1mbps')
    #bandwidth.append('10mbps')
    #bandwidth.append('20mbps')
    #bandwidth.append('30mbps')

    blmap = test()

    for i in range(1,len(blmap)+1):
        format_bandwidth = '%d kbps' % i
        bandwidth.append(format(format_bandwidth))
        latency.append(blmap[i])
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ind = np.arange(len(blmap))
    
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

def test():
    i = 1
    blmap = dict()
    files = ['100_kb_output.txt', '1kb_output.txt', '10kb_output.txt']
    
    for file in files:
        with open(file, 'r') as f:
            data  = list()
            group = dict()
            
            for latency in re.findall('[[0-9.]*]', f.read()):
                latency = string.strip(latency, '[]')
                #print latency
                blmap[i] = latency
                
            i = i+1

    return blmap
            
    
if __name__ == '__main__':
    graph_latency()
    #test()
