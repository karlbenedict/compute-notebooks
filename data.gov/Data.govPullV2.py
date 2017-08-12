
# coding: utf-8

# In[1]:

import urllib.request
import datetime
import json
import os
import uuid
import requests


# In[2]:

# set default variables for subsequent runs
requestSize = 1000
requestLimit = 1000
requestBaseURL = "https://catalog.data.gov/api/3/action"
requestFunction = "package_search"
dataBaseDirectory = "Data.gov_Files"


# In[15]:

class Harvest:
    '''
    A class representing a specific harvest of metadata
    '''
    
    def __init__(self,requestSize,requestLimit,requestBaseURL,requestFunction,dataBaseDirectory):
        '''
        Create a new harvest instance
        The class is initialized with the following parameters
          * requestSize - the number of datasets that should be included in each request
          * requestLimit - the maximum number of requests that should be made (a small number for this can be used for testing purposes)
          * requestBaseURL - the URL that is common to all requests being submitted
          * requestFunction - the API function that is being called for the specific harvest run
          * dataBaseDirectory - the base directory location (without following "/") where the retrieved files should be stored
          
        '''
        self.requestSize = requestSize
        self.requestLimit = requestLimit
        self.requestBaseURL = requestBaseURL
        self.requestFunction = requestFunction
        self.dataBaseDirectory = dataBaseDirectory
        self.timestamp = datetime.datetime.now()
        self.timestring = '{:%Y-%m-%dT%H:%M:%S}'.format(self.timestamp)
        self.saveDirectory = self.dataBaseDirectory + '/' + self.timestring
        self.runID = str(uuid.uuid4())
        self.logfile = self.saveDirectory + '/' + self.timestring + '_' + self.runID  + ".log"
        self.testResults = self.saveDirectory + "/" + self.timestring + '_' + self.runID  + "_testResults.txt" 
        self.resourceList = self.saveDirectory + "/" + self.timestring + '_' + self.runID  + "_resources.txt"
        self.testURLs = self.saveDirectory + "/" + self.timestring + '_' + self.runID  + "_testURLs.json"
        self.fileList = []
        self.testList = []
        self.testCount = 0
        #self.testResults = []
        #self.resourceList = {}
        os.makedirs(self.saveDirectory, exist_ok=True)
        
        self.writeLog(self.logfile,'Harvest Run')
        self.writeLog(self.logfile,'\tinitiated: ' + self.timestring)
        self.writeLog(self.logfile,'\tharvest ID: ' + self.runID)
        self.writeLog(self.logfile,'\trequestSize: ' + str(self.requestSize))
        self.writeLog(self.logfile,'\trequestLimit: ' + str(self.requestLimit))
        self.writeLog(self.logfile,'\trequestBaseURL: ' + self.requestBaseURL)
        self.writeLog(self.logfile,'\trequestFunction: ' + self.requestFunction)
        self.writeLog(self.logfile,'\tdataBaseDirectory: ' + self.dataBaseDirectory)
        
        self.initialize()
        
        
    def writeLog(self,filePath,message):
        with open(filePath,'a') as f:
            f.write('{:%Y-%m-%dT%H:%M:%S}'.format(datetime.datetime.now()) + '\t')
            f.write(message+"\n")
    
    def initialize(self):
        self.initStartTime = datetime.datetime.now()
        logMessage = "Initialization Process Started "
        self.writeLog(self.logfile,logMessage)
        self.harvest()
        self.extractResources()
        self.initEndTime = datetime.datetime.now()
        logMessage = "Initialization Process Complete: " + str(self.initEndTime - self.initStartTime)
        self.writeLog(self.logfile,logMessage)
    
    def harvest(self):
        startTime = datetime.datetime.now()
        logMessage = "Harvest Initiated"
        self.writeLog(self.logfile,logMessage)
        i=0
        numDataSets = 0
        finished = False
        while not finished:
            requestString = self.requestBaseURL + "/" + self.requestFunction + "?" + "rows=" + str(self.requestSize) + "&" + "start=" + str(i*self.requestSize)
            logMessage = str(i) + ".\tgetting: " + requestString
            self.writeLog(self.logfile,logMessage)

            outFilePath = self.saveDirectory + "/" + self.runID + "_" + self.timestring + "_" + '{0:08d}'.format((i*self.requestSize)+1) + "-" + '{0:08d}'.format(((i+1)*self.requestSize)) + ".json"
            logMessage = "\toutput file path: " + outFilePath
            self.writeLog(self.logfile,logMessage)

            with urllib.request.urlopen(requestString) as JSONfile:    
                resultString = JSONfile.read().decode('utf-8')
                numDataSets = json.loads(resultString)['result']['count']
                with open(outFilePath, "w") as f:
                    f.write(resultString)
            self.fileList.append(outFilePath)
            i += 1
            logMessage = "\tFinished processing: " + outFilePath
            self.writeLog(self.logfile,logMessage)
            logMessage = "\t" + str(i*self.requestSize) + " out of " + str(numDataSets) + " processed"
            self.writeLog(self.logfile,logMessage)
            if i >= requestLimit: finished = True
            if i*requestSize > numDataSets: finished = True
        endTime = datetime.datetime.now()
        self.writeLog(self.logfile,"Harvest Completed")
        logMessage = "Harvest Execution Time: " + str(endTime - startTime)
        self.writeLog(self.logfile,logMessage)

    def extractResources(self):
        startTime = datetime.datetime.now()
        logMessage = "\t".join(["entryID","orgTitle","orgName","orgID","name","metadataCreated","metadataModified","resourceType","resourceID","created","mimetype","url", "extras"])
        self.writeLog(self.resourceList,logMessage)
        for filePath in self.fileList:
            with open(filePath) as JSONfile:
                logMessage = "Extracting resources from: " + filePath
                self.writeLog(self.logfile,logMessage)
                JSONdict = json.loads(JSONfile.read())

                for result in JSONdict['result']['results']:
                    entryID = str(uuid.uuid4())
                    orgTitle = result["organization"]["title"]
                    orgName = result["organization"]["name"]
                    orgID = result["organization"]["id"]
                    name = result["name"]
                    notes = result["notes"]
                    metadataCreated = result["metadata_created"]
                    metadataModified = result["metadata_modified"]
                    resourceType = result["type"]
                    extras = result["extras"]
                    entryResources = {}
                    logMessage = "Identified Resources for: " + orgName + "(" + entryID + ")"
                    self.writeLog(self.logfile,logMessage)
                    for resource in result['resources']:
                        resourceID = str(uuid.uuid4())
                        created = resource["created"]
                        mimetype = resource["mimetype"]
                        url = resource["url"]
                        resourceInfo = {resourceID:{"created":created, "mimetype":mimetype, "url":url}}
                        #entryResources.update(resourceInfo)
                        #self.writeLog(self.resourceList,str(resourceInfo))
                        self.testResource([resourceID,url])
                        logMessage = "\tTesting elapsed time: " + str(datetime.datetime.now() - startTime) + ":\t" + resourceID + ", " + url
                        self.writeLog(self.logfile,logMessage)
                        logMessage = "\t".join([entryID,orgTitle,orgName,orgID,name,metadataCreated,metadataModified,resourceType,resourceID,created,str(mimetype),url,str(extras)])
                        self.writeLog(self.resourceList,logMessage)
                    #with open(self.resourceList, "a") as f:
                    logMessage =  "\t" + str({entryID:{"orgTitle":orgTitle, "orgName":orgName, "orgID":orgID, "name":name, "metadata_created":metadataCreated, "metadata_modified":metadataModified, "resourceType":resourceType, "extras":extras, "resourcesURLs":entryResources}})
                    self.writeLog(self.logfile,logMessage)
        endTime = datetime.datetime.now()
        self.writeLog(self.logfile,"URL Test Completed")
        logMessage = "URL Test Execution Time: " + str(endTime - startTime)
        self.writeLog(self.logfile,logMessage)
        
                                        
                    
    def testResource(self,resourceList):
        self.testCount += 1
        logMessage = "%s. Checking %s, (%s)"%(self.testCount,resourceList[0], resourceList[1])
        self.writeLog(self.logfile,logMessage)
        try:
            status = requests.head(resourceList[1], timeout=1 )
            logMessage = "\tchecked: " + resourceList[1]
            self.writeLog(self.logfile,logMessage)
            logMessage = "\tstatus: " + str(status)
            self.writeLog(self.logfile,logMessage)
        except requests.exceptions.ConnectionError as e:
            logMessage = "\tConnection Error: " + resourceList[1]
            self.writeLog(self.logfile,logMessage)
            status = "failed - connection error - " + str(e)
        except requests.exceptions.Timeout as e:
            logMessage = "\tTimeout Error: " + resourceList[1]
            self.writeLog(self.logfile,logMessage)
            status = "failed - timeout - " + str(e)
        except requests.exceptions.RequestException as e:
            logMessage = "\tRequest Exception Error: " + str(e) + " -  " + resourceList[1]
            self.writeLog(self.logfile,logMessage)
            status = "failed - request exception - " + str(e)
        except requests.exceptions.InvalidSchema as e:
            logMessage = "\tNon-HTTP request error: " + str(e) + " -  " + resourceList[1]
            self.writeLog(self.logfile,logMessage)
            status = "failed - Non-HTTP request - " + str(e)
        except:
            logMessage = "\tOther error: " + resourceList[1]
            self.writeLog(self.logfile,logMessage)
            status = "failed - Other error"


            
        
        logMessage = "%s\t%s\t%s"%(resourceList[0],resourceList[1],str(status))
        self.writeLog(self.testResults,logMessage)


# In[16]:

testHarvest = Harvest(requestSize,requestLimit,requestBaseURL,requestFunction,dataBaseDirectory)


# In[ ]:




# In[ ]:



