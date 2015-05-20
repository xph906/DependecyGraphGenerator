==What the screenshots plugin does==

It blocks on requests coming through the mitmproxy and then takes screenshots before the next requests is allowed to come through.  It then compares the current screenshot with the one before to see if there is a significant difference.  If there is a significant difference it sends a message to port 8080 on localhost to tell the parent program to stop the mitmproxy because the user perceived location in the request queue was found.

==screenshot-firefox-driver.py==

This file drives the firefox browser as well as the mitmproxy application.  It first takes in a few parameters.

-f <type of visit to websites proxyvisit/normalvisit>
-fu <website the visit first>
-t <number of times to visit>
-c <configure file>
-d <directory where logs should be stored>

Example Call:
python screenshot-firefox-driver.py -f proxyvisit -fu http://www.cnn.com/ -t 5 -c screenshot_configure -d ./logs/

This can obviously be rewritten to take direct argument parameters instead of a configure file, but at the moment this is not supported.

The script starts by reading the parameters given, it reads the configure file, it starts the browser, it enters a loop which starts and stops the mitmproxy while visiting the website given in between, then after all the times are done then it stops the browser and the whole script is done. 

==screenshot-script.py==

This is the mitmproxy script that does all the magic.  It also takes a few paramters but simply as a list of arguments.  Because it is called by the screenshot-firefox-driver.py script, the sys.argv list is offset by 2 because in the argument call, the script's name itself is technically the first argument.

The argument list must be contained entirely within the 3rd argument as shown on the next line
arglist = sys.argv[2].split(" ")

In the script, it follows to take off the parts of the split up string as the real arguments to the proxy script.
logDir = arglist[1]
thresholdLow = float(arglist[2])
thresholdHigh = float(arglist[3])
secondsBetweenRequests = int(arglist[4])
logName = arglist[5]

==screenshot_configure==
This is a JSON file that serves as configuration for the screenshot-firefox-driver.py and screenshot-script.py script.  The first piece of configuration is the only one directly used by the driver script and is very important - its value MUST be replaced on each installation.

"firefoxProfilePathWithProxy": <must be the full path to the proxy directory>
"mitmproxyScriptPath": "./screenshot-script.py",
"logDir": "./logs",
"thresholdLow": "0.75",
"thresholdHigh": "0.85",
"secondsBetweenRequests": "5"

The fields themselves are self explanatory.


