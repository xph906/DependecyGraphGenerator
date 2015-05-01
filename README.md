# dependency graph generator
Scripts:
proxy-script.py: inline script of mitmproxy
firefox-driver.py: selenium script
LogAnalysis.py: create dependecy graph based on bro traces

## Required packages
1. pip
   install pip at https://bootstrap.pypa.io/get-pip.py

2. mitmproxy:
The proxy you will use.
```
pip install mitmproxy
```

3. Network Link Conditioner:
Control the bandwidth and other network condition.Download at https://developer.apple.com/downloads/index.action?q=Network%20Link%20Conditioner#

4. Bro:
Monitor all the traffic.

5. ipfw:
programmatically control the bandwidth and other network condition.



  
## Brief steps

Take Wall street journal (http://www.wsj.com) for example. 
1. Set firefox proxy profile

2. run proxy visit and get logs
  ```
  python firefox-driver.py -f proxyvisit  -fu http://www.wsj.com -t 15 -c air_configure -p WSJ
  ```
3. get common urls
          running firefox for several times with 
          input: first url
          output: common url list
```
 python LogAnalysis.py -f getcommonurl -d logs -p WSJ -ho test          
```
4. get dependency graph
          run firefox multiple times with proxy, each time, one url will be suspended for a long time and these urls are from common url list
          input: common url list
          output: dependency graph
```
python LogAnalysis.py -f generategraph -p WSJ -d ./logs/ -fu http://www.wsj.com/ -go wsjGraph -lu
http://video-api.wsj.com/api-video/player/v2/css/wsjvideo.min.css -c wsjHostList  
```
5. calculate user-perceived delay in different network conditions
          On each network condition, run firefox multiple times without proxy, use bro to monitor, record important information of traffic and get bro log. Then analyze bro log using script.
          input: common url list, dependency graph, first url, last url
          output: user perceived delay for each network condition
```
sudo bro -i en0 -C httpinfo.bro > test.txt
python LogAnalysis.py -f analyzebrolog -fu http://www.wsj.com/ -lu http://video-api.wsj.com/api-video/player/v2/css/wsjvideo.min.css -gi wsjGraph -c wsjHostList -b broscript/test.txt
```
6. propose prediction module.

