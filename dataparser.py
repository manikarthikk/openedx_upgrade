from collections import OrderedDict
import re
from subprocess import call
import sys, getopt
import os 

# search pattern
pattern = r'Applying (.\w*).(.*?)... OK'
SEPARATOR = "."

def processLog(fileName):
  ctr = 0
  lmsDict = OrderedDict()
  cmsDict = OrderedDict()

  with open(fileName, 'r') as searchfile:
    for line in searchfile:
      # print(line)
      if line.find("Running deferred SQL") > 0 : # if the line contains Running deferred SQL tag it
        ctr = ctr + 1

      if ctr == 1:    #process as LMS
        processLine(lmsDict, line, "LMS")
      elif ctr == 2:  #process as CMS  
        processLine(cmsDict,line, "CMS")
      
  #compare the two sets, remove duplicates from CMS before processing 
  if len(lmsDict) > 0 and len(cmsDict) > 0 :  #at least one entry should be there in both dicts
    dupDict = compareDict(lmsDict, cmsDict)

  #now print the summary of each dictionary      
  printSummary(lmsDict, "LMS")
  printSummary(cmsDict, "CMS")
  printSummary(dupDict, "Duplicates")

  writeToFile("lms_upgrade.log", lmsDict, "LMS")
  writeToFile("cms_upgrade.log", cmsDict, "CMS")
  writeToFile("duplicates.log", dupDict, "Duplicates")

# takes 2 parameters line and dictionary
def processLine(d, line, label):
  pattern = r'Applying (.\w*).(.*?)... OK'
  #print("processLine:", label, line)
  if "Applying" in line: 
    searchObj = re.search(pattern, line, re.M|re.I)
    if (searchObj):
        appName = searchObj.group(1)    #example - api_admin
        group2 = searchObj.group(2)
        ptr = group2.index("_")
        migrationNumber = group2[ : ptr]   #example - 0001 (any number)
        description = group2[ptr+1:]
        # the key is unique in the dictionary
        # key + value = file example api_admin.002_auto_20160325_1604
        # ideally I want this to be an object later on (class)
        key = appName + SEPARATOR + migrationNumber #example - api_admin.0001 
        # print(key)
        value = description        #example - api_admin.0002_auto_20160325_1604
        # print(key+ SEPARATOR + value)
        d[key] = value

# for each entry in lmsDict check if it exists in cmsDict
# if it is there remove it from cmsDict
def compareDict(lmsDict, cmsDict):
  duplicates = OrderedDict()
  for key, value in lmsDict.items():
    if key in cmsDict:
      duplicates[key] = value
      del cmsDict[key]
  return duplicates

#function to print the summary
def printSummary(d, label):
  print("=========="+ label + "==========")
  s = 'Total number of migrations of {} = {}'.format(label, len(d))
  print(s)
  printDetails(d)

# function to print the statistics
def printDetails(d):
  if len(d) > 0:
    for key, value in d.items():
      appName, migrationNumber = parseKey(key)
      print(appName, migrationNumber)
  else:
      print("There are no migrations")

# function to parse appName and migration number
# given a key like microsite_configuration.0001

def parseKey(key):
  index = key.index(".")
  appName = key[0:index]
  migrationNumber = key[index + 1:]
  return appName, migrationNumber

#function to write contents to file
#by default the file is written in text mode 
#if the file is 
def writeToFile(filename, d, label):
  if filename is None:
    filename = label + ".sql"
  with open(filename, "w+") as f:
    for key, value in d.items():
      appName, migrationNumber = parseKey(key)
      f.write(appName + "\t"+ migrationNumber + "\n")
  print("done writing ::", label)


# it should take the full path of the filename
# check for main and help should be included..
processLog('upgrade.log')
os.system('bash sqlmigrate_lms.sh')
os.system('bash sqlmigrate_cms.sh')

#call(["bash", "sqlmigrate_lms.sh"]) && call(["bash", "sqlmigrate_cms.sh"])



