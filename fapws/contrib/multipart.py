import os.path

class Storage(object):
    def __init__(self):
        self.fpath=None
    def open(self, attr):
        pass
    def write(self, data):
        pass
    def close(self):
        self.fpath=None #self.fpath allow us to know if the storage repository has to write some data or not

class DiskStorage(Storage):
    def open(self, fpath):
        self.fpath=fpath
        if self.fpath:
            self.fid=open(self.fpath,"wb")
        else:
            raise ValueError("fpath is not declared")
    def write(self, data):
        if self.fid:
            self.fid.write(data)
        else:
            raise ValueError("First open before writing")
    def close(self):
        self.fpath=None
        if self.fid:
            self.fid.close()
        
class DiskVersioning(DiskStorage):
    def _definefilename(self, fpath):
        "This method avoid the overwrite syndrome"
        if os.path.isfile(fpath):
            base,ext=os.path.splitext(fpath)
            res=base.rsplit('_',1)
            if len(res)==1:
                version="0"
                name=res[0]
            else:
                name,version=res
            return self._definefilename(name+"_"+str(int(version)+1)+ext)
        return fpath
    def open(self, fpath):
        self.fpath=self._definefilename(fpath)
        if self.fpath:
            self.fid=open(self.fpath,"wb")
        else:
            raise ValueError("fpath is not declared")

class GitStorage(Storage):
    "Still to develop"
    
    
class DBstorage(Storage):
    "still to develop"
    
    

class MultipartFormData(object):
    """This class allow you to read, on the fly, the multipart elements we useually find in wsgi.input.
       file like objects are stored on the fly on disk, parameters are strored in .results dictionary
       For a specific parameter, and if required, an extra dictionary containing additinal info is appended.
       Feel free to adapt the self.definefilename. As default, we use the versioning. 
    """
    def __init__(self, basepath="./"):
        "Just provide the directory path where the file objects must be stored" 
        self.basepath=basepath
        self.results={}
        self.boundary=None
        self._inheader=False
        self.filerepository=DiskVersioning() #per default we use the versioning method
    def write(self, data):
        #data can be chunk of the input data or all the input data
        line=b""
        prevchar=b""
        paramkey=b""
        paramvalue=b""
        paramattr={}
        content=b""
        data_len = len(data)
        for pos in range(data_len):
            char = data[pos:pos+1] 
            line+=char
            if char==b"\n" and prevchar==b"\r":
                if self.boundary==None and line[:2]==b"--":
                    #we have found a boudary. This will be used for the rest of the parser
                    self.boundary=line.strip()
                if self.boundary in line:
                    self._inheader=True
                    if content and not paramvalue:
                        paramvalue=content.strip()
                    if self.filerepository.fpath:
                        #we have to close the previous outputfid
                        self.filerepository.close()
                        paramattr[b'size']=os.path.getsize(paramvalue)
                    if paramkey:
                        self.results.setdefault(paramkey,[])
                        self.results[paramkey].append(paramvalue)
                        if paramattr:
                            self.results[paramkey].append(paramattr)
                    content=b""
                    paramvalue=b""
                    paramattr={}
                elif line.strip()==b"" and self._inheader:
                    self._inheader=False
                elif self._inheader:
                    key,val=[x.strip() for x in line.split(b':')]
                    if key==b"Content-Disposition" and val[0:10]==b"form-data;":
                        for elem in val[11:].split(b';'):
                            pkey,pval=[x.strip() for x in elem.split(b'=')]
                            if pval[0:1]==b'"' and pval[-1:]==b'"':
                                pval=pval[1:-1]
                            if pkey==b"filename":
                                if pval:
                                    pval = pval.decode('utf8')
                                    self.filerepository.open(self.basepath+pval)
                                    paramvalue=self.filerepository.fpath
                            elif pkey==b"name":
                                paramkey=pval
                            else:
                                paramattr[pkey]=pval
                    else:
                        paramattr[key]=val
                elif not self._inheader:
                    if self.filerepository.fpath:
                        self.filerepository.write(line)
                    else:
                        content+=line
                line=b""
            prevchar=char
    def seek(self, position):
        #required for compatibility with file like object
        pass
    def getvalue(self):
        return self.results
    def get(self, key):
        return self.results.get(key, None)
    def keys(self):
        return list(self.results.keys())
    

