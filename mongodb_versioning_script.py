
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient()

db = client.edxapp

collection = db.modulestore.active_versions
required_version_list=[]
available_version_list = []
for value in collection.find({ }, { "versions.draft-branch": 1,"versions.published-branch": 1,"versions.library": 1,}):
    required_version_list.append(value)
versions = [d['versions'] for d in required_version_list]
for value in versions:
    if u'library' not in value:
        value.update({u'library': None})
    elif u'draft-branch' not in value:
        value.update({u'draft-branch':None})
        value.update({u'published-branch':None})
for j in db.modulestore.structures.find({ },{"previous_version":1} ):
    available_version_list.append(j)

draft_branch_version = [version_dict['draft-branch'] for version_dict in versions]
published_branch_version = [version_dict['published-branch'] for version_dict in versions]
library_branch_version = [version_dict['library'] for version_dict in versions]
all_required_versions = draft_branch_version+published_branch_version+library_branch_version
all_req_versions = [version for version in all_required_versions if version != None ]
print "********** all required versions **********"
print all_req_versions

def search_dictionaries(key, value, list_of_dictionaries):
    for element in list_of_dictionaries:
        if element[key] == value:
            return element

def mongo_version_manager():
    for verions in all_req_versions:
        var1  = search_dictionaries('_id',verions,available_version_list)
        i = 0
        version_tree = []
        while  var1['previous_version'] != None:
            var1 = search_dictionaries('_id',var1['previous_version'],available_version_list)
            if var1 == None:
               break
            version_tree.append((i,var1))
            i = i+1
            print var1
        if len(version_tree) > 3:
            a = []
            i = 2
            b = []
            
            b.append(version_tree[2][1].values()[1])
            a.append(version_tree[-2][1].values()[1])
            versions_tobe_deleted = []
            for i in range(3,len(version_tree)-2):
                versions_tobe_deleted.append(version_tree[i][1]['_id'])     
            print "**********versions to be deleted*******************"
            print versions_tobe_deleted 
            print a 
            print b
            print "a nad b valaues above"           
            #print version_tree[2:-2][1][2].values()[0]
            db.modulestore.structures.update({ '_id': {'$in':b}}, { '$set': { "previous_version" : a[0]}   })
            db.modulestore.structures.remove({'_id':{'$in':versions_tobe_deleted}})
            print "************** the below versions are deleted***********************"
            print versions_tobe_deleted
        else:
            print "did not go to for loop as it is not > 2"
        
    return version_tree
a = mongo_version_manager()
