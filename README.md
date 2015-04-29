# dependency graph generator
Scripts:
proxy-script.py: inline script of mitmproxy
firefox-driver.py: selenium script
LogAnalysis.py: create dependecy graph based on bro traces

## Required packages
1. mitmproxy:
this is the proxy you will use. 

2. Network Link Conditioner:
control the bandwidth and other network condition.

3. Bro:
Monitor all the traffic.

4. ipfw:
programmatically control the bandwidth and other network condition.



  
## Brif steps
1. get common urls
          running firefox for several times with 
          input: first url
          output: common url list
          
2. get dependency graph
          run firefox multiple times with proxy, each time, one url will be suspended for a long time and these urls are from common url list
          input: common url list
          output: dependency graph

3. calculate user-perceived delay in different network conditions
          On each network condition, run firefox multiple times without proxy, use bro to monitor, record important information of traffic and get bro log. Then analyze bro log using script.
          input: common url list, dependency graph, first url, last url
          output: user perceived delay for each network condition

4. propose prediction module.												    4. propose prediction module.
