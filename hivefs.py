#!/usr/bin/env python

from sys import argv, exit
from errno import *
import errno
from addict import Dict
import sys
import requests
import json
import stat
import time
import os
import getpass

from fuse import FUSE, Operations, LoggingMixIn
import fuse
from pprint import pprint

s = requests.Session()

class Hive(Operations):

    def __init__(self, test="testing", path='.'):
        self.email = input("Email: ")
        self.pw = getpass.getpass()
        self.data={'ip': 'MTkyLjE3MS40MC4xNg==', 'password': self.pw, 'email': self.email}
        self.headers={'Client-Type': 'Browser', 'Client-Version': '0.1', 'User-Agent': 'hivefs'}
        self.loginurl='https://api.hive.im/api/user/sign-in/'
        self.tldurl = 'https://api.hive.im/api/hive/get/'
        self.getchildrenurl = 'https://api.hive.im/api/hive/get-children/'
        self.updateurl = 'https://api.hive.im/api/hive/update/'
        self.createurl = 'https://api.hive.im/api/hive/create/'
        self.userdata = Dict()
        self.tldData = {}
        self.tldFolders = Dict()
        self.folderData = Dict()
        self.login()

    def login(self):
        l = s.post(self.loginurl, data=self.data, headers=self.headers)
        self.userdata = Dict(json.loads(l.text))
        if self.userdata.status == 'error':
            print("Login Failed!")
            exit()

        self.headers['Authorization'] = self.userdata['data']['token']
        r = s.get(self.tldurl, headers=self.headers)
        self.tldFolders = Dict(json.loads(r.text))
        for folder in self.tldFolders.data:
            self.folderData[folder.title] = Dict({'_id': folder.id, '_folder': folder.folder, '_locked': folder.locked})

        self.folderData.prune()
        pprint(self.folderData)
        
    def getMetadata(self, path):
        print("Looking for "+path+" METADATA")
        pathlist = path.split('/')
        pathlist.remove('')
        currentFolder = self.folderData
        
        for item in pathlist:
            if item in list(currentFolder.keys()):
                currentFolder = currentFolder[item]
            else:
                return 0
                
        print("...got METADATA for "+path)
        return currentFolder
        
        
    def updateMetadata(self, path, key, value):
        pathlist = path.split('/')
        pathlist.remove('')
        currentFolder = self.folderData
        
        for item in pathlist:
            if item in list(currentFolder.keys()):
                currentFolder = currentFolder[item]
                
        currentFolder[key] = value
        
        
    def getFolderId(self, path):
        print("Getting folder id for "+path)
        pathlist = path.split('/')
        pathlist.remove('')
        fileType = ""
        lastlen = ""
        print("pathlist: "+str(pathlist))
        print("last pathlist element: "+str(pathlist[len(pathlist)-1]))
        if len(pathlist) == 1:
            lastlen = len(str(pathlist[0]).split('.'))
        else:
            lastlen = len(str(pathlist[len(pathlist)-1]).split('.'))
            
        if lastlen > 1:
            fileType = "file"
            print(path+" is a file")
        else:
            print(path+" is a folder")
            fileType = "folder"
        
        if len(pathlist) == 1:
            pprint(self.folderData)
            return self.folderData[pathlist[0]]._id
        
        if fileType == "folder":
            dirpathlist = pathlist
        else:
            dirpathlist = pathlist[:len(pathlist)-1]
            
        print("dirpathlist: "+str(dirpathlist))
        currentFolder = self.folderData
        currentId = self.folderData[pathlist[0]]._id
        if currentId == {}:
            print("folder id for "+str(pathlist[0])+" does not exist.")
            return 0
        else:
            for item in pathlist:
            # Walking the folder tree...
                print("item: "+item+"    currentFolder.keys(): "+str(list(currentFolder.keys())))
                if item in list(currentFolder.keys()):
                # If we find the current part of the path in the currentFolder we're in...
                    currentFolder = currentFolder[item]
                    if currentFolder._id == {}:
                    # If the folder we're looking in now hasn't been looked in before (this session), enumerate it and create metadata entries.
                        r = s.post(self.getchildrenurl, data={'parentId': currentId}, headers=self.headers)
                        currentId = currentFolder._id
                        for item in Dict(json.loads(r.text)).data:
                            print("ITEM (first):")
                            pprint(item)
                        # For each file or folder found under the folder with id currentId...
                            if item.folder:
                            # If it's a folder, we create an entry for its title containing the id, a _folder boolean and whether it's locked.
                                currentFolder[item.title] = Dict({'_id': item.id, '_folder': item.folder, '_locked': item.locked})
                            else:
                            # If it's a file, we create an entry for its title containing the id, whether it's a folder, if it's locked, the file extension, date modified, date created, size, and the download url.
                                currentFolder[item.title+"."+item.extension] = Dict({'_id': item.id, '_folder': item.folder, '_locked': item.locked, '_extension': item.extension, '_dateModified': item.dateModified, '_dateCreated': item.dateCreated, '_size': item.size, '_download': item.download})
                            
                    else:
                        currentId = currentFolder._id
                else:
                # If we can't find the current part of the path in the currentFolder we're looking in, check and see if it exists on the server.
                    r = s.post(self.getchildrenurl, data={'parentId': currentId}, headers=self.headers)
                    for item in Dict(json.loads(r.text)).data:
                        print("ITEM (second):")
                        pprint(item)
                    # If the current part of the path exists on the server, enumerate its metadata and create metadata entries like above.
                        if item.folder:
                            currentFolder[item.title] = Dict({'_id': item.id, '_folder': item.folder, '_locked': item.locked})
                        else:
                            currentFolder[item.title+"."+item.extension] = Dict({'_id': item.id, '_folder': item.folder, '_locked': item.locked, '_extension': item.extension, '_dateModified': item.dateModified, '_dateCreated': item.dateCreated, '_size': item.size, '_download': item.download})
                        
                    if item in list(currentFolder.keys()):
                        currentFolder = currentFolder[item]
                        currentId = currentFolder._id
                    else:
                        print("Folder "+str(pathlist[len(pathlist)-1])+" does not exist.")
                        pprint(self.folderData)
                        return 0
                    
                    #return 0
            
            print("folder id for "+str(pathlist[len(pathlist)-1])+" is: "+str(currentId))
            # If we find what we're looking for, return the containing folder id. (might need to change this later)
            return currentId

    def chmod(self, path, mode):
        pathlist = path.split('/');
        pathlist.remove('')
        isLocked = "true"
        mdLocked = True
        if mode == 16832:
            isLocked = "true"
            mdLocked = True
        else:
            isLocked = "false"
            mdLocked = False
            
        if len(pathlist) > 1:
            md = self.getMetadata(path)
            if md._folder:
                r = s.post(self.updateurl, data={'filename': pathlist[-1], 'hiveId': md._id, 'locked': isLocked}, headers=self.headers)
                if json.loads(r.text)['status'] == "success":
                    #update metadata
                    self.updateMetadata(path, "_locked", mdLocked)


    def chown(self, path, uid, gid):
        print("Attempted chown ")#+str(uid)+" on "+path

    def create(self, path, mode):
        print("Attempted create ")#+path+" with "+str(mode)
    #    f = (TODO: Create and return a file object (after uploads are working))
    #    f.chmod(mode)
    #    f.close()
    #    return 0

    def destroy(self, path):
        print("Attempted destroy on ")#+path

    def getattr(self, path, fh=None):
        stats = dict()
        now = time.time()
        pathlist = path.split('/')
        pathlist.remove('')
    
        def processMetadata(metadata):
            print("Got METADATA for "+path)
            if metadata._folder and metadata._locked == False:
                print("folder not locked")
                stats['st_mode'] = 0o744 | stat.S_IFDIR
            elif metadata._folder and metadata._locked == True:
                print("folder locked")
                stats['st_mode'] = 0o700 | stat.S_IFDIR
            elif metadata._folder == False and metadata._locked == False:
                print("file not locked")
                stats['st_mode'] = 0o744 | stat.S_IFREG
            else:
                print("file locked")
                stats['st_mode'] = 0o700 | stat.S_IFREG
                
            if metadata._dateModified == {}:
                stats['st_mtime'] = now
            else:
                stats['st_mtime'] = int(time.mktime(time.strptime(metadata._dateModified, '%Y-%m-%d %H:%M:%S')))
                
            if metadata._dateCreated == {}:
                stats['st_ctime'] = now
            else:
                stats['st_ctime'] = int(time.mktime(time.strptime(metadata._dateCreated, '%Y-%m-%d %H:%M:%S')))
                
            if metadata._folder or len(pathlist) == 1:
                stats['st_size'] = 0
            else:
                stats['st_size'] = int(metadata._size)
                
            stats['st_uid'] = os.getuid()
            return stats
        
        if path == "/":
            stats['st_mode'] = 0o744 | stat.S_IFDIR
            stats['st_size'] = 0
            stats['st_uid'] = os.getuid()
            stats['st_mtime'] = now
            stats['st_ctime'] = now
            stats['st_gid'] = os.getgid()
            return stats
        
        print("Checking (1) for METADATA for "+path)
        md = self.getMetadata(path)
        if md != 0:
        # If we found metadata for the item we're looking for...
            return processMetadata(md)
        
        print("Did NOT get metadata for "+path)
        dirId = self.getFolderId(path)
        print("Got dirId "+str(dirId)+" for "+str(path))
        print("Trying METADATA again: ")
        md = self.getMetadata(path)
        if md != 0:
        # If we found metadata for the item we're looking for...
            return processMetadata(md)
        #pprint(self.getMetadata(path))
        
        if dirId == 0 or dirId == {}:
            raise fuse.FuseOSError(errno.ENOENT)
        else:
            r = s.post(self.getchildrenurl, data={'parentId': dirId}, headers=self.headers)
            try:
                contents = json.loads(r.text)['data']
            except ValueError:
                stats['st_mode'] = 0o744 | stat.S_IFDIR
                stats['st_mtime'] = now
                stats['st_size'] = 0
                stats['st_uid'] = os.getuid()
                stats['st_ctime'] = now
                stats['st_gid'] = os.getgid()
                return stats
                
            if contents == []:
                stats['st_mode'] = 0o744 | stat.S_IFDIR
                stats['st_mtime'] = now
                stats['st_size'] = 0
                stats['st_uid'] = os.getuid()
                stats['st_ctime'] = now
                stats['st_gid'] = os.getgid()
                print("Looks like an empty folder.")
                return stats
            
            for item in contents:
                if item['title'] == ".".join(pathlist[len(pathlist)-1].split('.')[:-1]):
                    print("if title is: "+".".join(pathlist[len(pathlist)-1].split('.')[:-1]))
                    if item['folder'] == True and item['locked'] == False:
                        print("folder not locked")
                        stats['st_mode'] = 0o744 | stat.S_IFDIR
                    elif item['folder'] == True and item['locked'] == True:
                        print("folder locked")
                        stats['st_mode'] = 0o700 | stat.S_IFDIR
                    elif item['folder'] == False and item['locked'] == False:
                        print("file not locked")
                        stats['st_mode'] = 0o744 | stat.S_IFREG
                    else:
                        print("file locked")
                        stats['st_mode'] = 0o700 | stat.S_IFREG
                        
                    stats['st_mtime'] = int(time.mktime(time.strptime(item['dateModified'], '%Y-%m-%d %H:%M:%S')))
                    stats['st_ctime'] = int(time.mktime(time.strptime(item['dateCreated'], '%Y-%m-%d %H:%M:%S')))
                    stats['st_size'] = int(item['size'])
                    stats['st_uid'] = os.getuid()
                    print(str(path)+" "+str(stats))
                    return stats
                else:
                    stats['st_mode'] = 0o744 | stat.S_IFDIR
                    stats['st_mtime'] = now
                    stats['st_size'] = 0
                    stats['st_uid'] = os.getuid()
                    stats['st_ctime'] = now
                    stats['st_gid'] = os.getgid()
            
        print(str(path)+" "+str(stats))
        return stats


    def mkdir(self, path, mode):
        print("Attempted mkdir on ")#+path+" with "+str(mode)
        fid = self.getFolderId(path)
        r = s.post(self.createurl, data={'filename': path.split('/')[-1], 'parent': fid, 'locked': False}, headers=self.headers)
    #    return self.sftp.mkdir(path, mode)

    def read(self, path, size, offset, fh):
        print("Attempted read on "+path) #+" with size="+str(size)+" offset="+str(offset)+" fh="+str(fh)
        md = self.getMetadata(path)
        if md != 0:
            rangeHeaders = self.headers
            rangeHeaders['Range'] = 'bytes='+str(offset)+'-'+str(offset+size-1)
            r = s.get(md._download, headers=rangeHeaders, stream=True)
            return r.content

    def readdir(self, path, fh):
        self.folderData.prune()
        if path == "/":
            return ['.', '..'] + list(self.folderData.keys())
        else:
            dirId = self.getFolderId(path)
            r = s.post(self.getchildrenurl, data={'parentId': dirId}, headers=self.headers)
            contents = json.loads(r.text)['data']
            items = []
            for item in contents:
                if item['folder'] == False:
                    items.append(item['title']+"."+item['extension'])
                else:
                    items.append(item['title'])
                    
            return ['.', '..'] + items
            

    #def readlink(self, path):
    #    return self.sftp.readlink(path)

    def rename(self, old, new):
        newlist = new.split('/')
        newlist.remove('')
        oldlist = old.split('/')
        oldlist.remove('')
        md = self.getMetadata(old)
        r = s.post(self.updateurl, data={'filename': newlist[-1], 'hiveId': md._id, 'locked': md._locked}, headers=self.headers)
        if json.loads(r.text)['status'] == "success":
            currentFolder = self.folderData
        
            for item in oldlist:
                if item in list(currentFolder.keys()):
                    if item == oldlist[-1]:
                        # update metadata like this because updateMetadata only works on element attributes right now.
                        currentFolder[newlist[-1]] = currentFolder.pop(oldlist[-1])
                    else:
                        currentFolder = currentFolder[item]
                            

    #def rmdir(self, path):
    #    return self.sftp.rmdir(path)

    #def symlink(self, target, source):
    #    return self.sftp.symlink(source, target)

    #def truncate(self, path, length, fh=None):
    #    return self.sftp.truncate(path, length)

    #def unlink(self, path):
    #    return self.sftp.unlink(path)

    #def utimens(self, path, times=None):
    #    return self.sftp.utime(path, times)

    def write(self, path, data, offset, fh):
        print("Attempted write to ")#+path
    #    f = self.sftp.open(path, 'r+')
    #    f.seek(offset, 0)
    #    f.write(data)
    #    f.close()
    #    return len(data)


if __name__ == '__main__':
    #if len(argv) != 3:
    #    print('usage: %s <host> <mountpoint>' % argv[0])
    #    exit(1)

    fuse = FUSE(Hive(), argv[1], foreground=True, nothreads=True)
