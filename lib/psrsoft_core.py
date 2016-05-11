import sys
import os,shutil
import logging
import argparse
import re
import fnmatch
import os
import uuid
import requests
import tarfile

__version__="2.0.0"

class psrsoft(object):
    def __init__(self,args):
        self.args=args
        self.pkgcache=[]
        self.cfg = config(args.cfg)

    def run(self):
        import psrsoft_automake
        package.types["automake"] = psrsoft_automake.package
        logging.debug("PkgTypes: "+", ".join(package.types.keys()))
        self.buildpkgcache()
        #self.install("tempo2")
        
        i,b,l,s = self.getpaths(self.pkgcache[1])
        self.pkgcache[1].build(i,b,s)

    def install(self,pstring):
        installlist=[]
        for p in pstring.split():
            ptag = tag(p)
            options = self.find(ptag)
            logging.debug(options)
            c = self.userchoice(options)
            if c:
                installlist.append(c)
            else:
                logging.error("invalid choice")
                return


        print installlist    

    def userchoice(self,options,txt="Please choose from the following:"):
        if len(options) < 1:
            return None
        elif len(options) < 2:
            return options[0]

        print txt
        d=1
        for o in options:
            print "%d) %s"%(d,o)
            d+=1
        ret = raw_input(" >>> ").strip()
        try:
            v = int(ret)
            if v == 0 or v > len(options):
                return None
            else:
                return options[v-1]
        except ValueError:
            logging.warning("Invalid integer '%s'"%ret)
            return None



    def find(self,t):
        ret=list()
        for p in self.pkgcache:
            if t.compare(p.tag):
                ret.append(p)
        return ret

    def getpaths(self,pkg):
        uid=uuid.uuid1()
        ipath = "%s/%s"%(self.cfg['installpath'],pkg.tag.asfilename())
        bpath = "%s/%s-%s"%(self.cfg['buildpath'],pkg.tag.asfilename(),uid)
        spath = "%s/%s-%s"%(self.cfg['srcpath'],pkg.tag.asfilename(),uid)
        lpath = "%s"%(self.cfg['linkpath'])

        return os.path.abspath(os.path.expandvars(ipath)),\
               os.path.abspath(os.path.expandvars(bpath)),\
               os.path.abspath(os.path.expandvars(lpath)),\
               os.path.abspath(os.path.expandvars(spath))


    def buildpkgcache(self):
        matches = []
        self.pkgcache = []
        for root, dirnames, filenames in os.walk('packages/'):
            for filename in fnmatch.filter(filenames, '*.package'):
                        matches.append(os.path.join(root, filename))
        for m in matches:
            with open(m) as f:
                pkg = package.parse(f)
                print m,pkg
                self.pkgcache.append(pkg)

class config(dict):
    def __init__(self,fname,load=True):
        self.desc = dict()
        self.desc['url'] = "Git URL for updating psrsoft."
        self['url']="https://github.com/SixByNine/psrsoft.git"
        self['installpath']="$psrsoft_dir/install"
        self['buildpath']="$psrsoft_dir/work/build"
        self['srcpath']="$psrsoft_dir/work/src"
        self['linkpath']="$psrsoft_dir/usr"

        self.defaultenv("make","make")
        self.defaultenv("cc","gcc")
        self.defaultenv("cxx","g++")
        self.defaultenv("f77","gfortran")
        self.defaultenv("editor","vi")
        if load:
            self.reload(fname)

    def defaultenv(self,k,v):
        if k.upper() in os.environ:
            self[k] = "$%s"%k.upper()
        elif k.lower() in os.environ:
            self[k] = "$%s"%k.lower()
        else:
            self[k] = v


    def reload(self,fname):

        kvregex=re.compile("\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s'\"#]+|\"[^\"]+\"|'[^']+')")
        try:
            with open(fname) as infile:
                for line in infile:
                    line = line.strip()
                    match = kvregex.match(line)
                    if match:
                        g=match.groups()
                        self[g[0]] = g[1]
        except IOError as e:
            logging.warning("Could not read config file '%s'"%fname)
            print "Do you want to try to create a new config file?"
            yn = raw_input("(y/n): ").strip()
            if yn.lower()=="y" or yn=="":
                print "Creating config file, '%s'"%fname
                try:
                    self.write(fname)
                    exe("$EDITOR %s"%fname)
                    self.reload(fname)
                except Error as e:
                    logging.error("Error creating file")
                    raise e

            else:
                logging.warning("Continuing with default configuration")
        for v in self:
            os.environ[v.upper()] = self[v]
            os.environ[v.lower()] = self[v]

    def write(self,fname):
        comp=config("",load=False)
        with open(fname,"w") as ofile:
            logging.debug("writing %s"%fname)
            for key in self.keys():
                logging.debug("key='%s'"%key)
                if self[key] == comp[key]:
                    c="# "
                else:
                    c=""
                if key in self.desc:
                    ofile.write("# %s\n"%(self.desc[key]))
                ofile.write("%s%s = %s\n\n"%(c,key,self[key]))
            ofile.close()



def exe(cmd):
    logging.debug("Exec '%s'"%cmd)
    ret=os.system(cmd)
    if ret==0:
        return True
    else:
        logging.warning("Command failed: %s"%cmd)
        return False


class packageoption(object):
    def __init__(self):
        pass


class tag(object):
    EQUAL="="
    LEQ="<="
    GEQ=">="
    tagre = re.compile("([A-Za-z0-9_-\.]+)\s*([<>]?=)\s*([A-Za-z0-9_-\.]+)|([A-Za-z0-9_-\.]+)[^=]*")

    def __init__(self,value):
        match = tag.tagre.match(value)
        if match:
            g = match.groups()
            if g[3] == None:
                self.name = g[0]
                self.type = g[1]
                self.version=g[2]
            else:
                self.name = g[3]
                self.type=""
                self.version=""
        else:
            logging.warning("bad version identifier '%s'"%value)

    def compare(self,other):
        if not other.name==self.name:
            return False
        if self.version=="" or other.version=="":
            return True
        vt1,vv1 = other.type,other.version
        vt2,vv2 = self.type,self.version

        # Trivial case
        if vt1 is tag.EQUAL and vt2 is tag.EQUAL:
            return vv1==vv2
        
        lhs = False
        rhs = False
        if vt2 is tag.LEQ:
            lhs = vt2 <= vt1

        if vt2 is tag.GEQ:
            lhs = vt2 >= vt1

        if vt1 is tag.LEQ:
            rhs = vt1 <= vt2

        if vt1 is tag.GEQ:
            rhs = vt1 >= vt2

        return lhs and rhs

    def __str__(self):
        return "%s %s %s"%(self.name,self.type,self.version)
    def __repr__(self):
        return self.asfilename()

    def asfilename(self):
        ret = "%s-%s"%(self.name,self.version)
        ret = re.sub(r"\s+", "_", ret, flags=re.UNICODE)
        return ret



class usingclause(object):
    def __init__(self,name):
        self.name=name
        self.requires=list()
        self.vars=dict()
        self.xlinks = list()
        self.desc=""
        self.sparelines=list()

    def __repr__(self):
        return "%s [%s]"%(self.name,self.desc)

class package(object):
    types=dict()

    def __init__(self):
        self.pkgtype="basic"
        self.sparelines = list()

        self.requires = list()
        self.usingclauses = dict()
        self.vars = dict()
        self.xlinks = list()
        self.currentclause=None
        self.kvregex=re.compile("\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\+?=)\s*([^\s'\"#]+|\"[^\"]+\"|'[^']+')")
        self.vars['linkpaths'] = ['bin']


    def __repr__(self):
        return self.tag.asfilename()

    def build(self,installdir,builddir,srcdir):
        # get the files!
        os.environ["srcdir"]=srcdir
        os.environ["builddir"]=srcdir
        os.environ["installdir"]=srcdir
        os.environ["PREFIX"]=installdir
        exe("mkdir -p %s"%builddir)
        exe("mkdir -p %s"%srcdir)
        exe("rm -rf %s && mkdir -p %s"%(installdir,installdir))
        exe("touch %s/env.sh %s/env.csh"%(installdir,installdir))

        if "export" in self.vars:
            for v in self.vars['export']:
                if v in self.vars:
                    os.environ[v]=' '.join(self.vars[v])
                    with open("%s/env.sh"%installdir,"a") as f:
                        f.write("export %s=\"%s\""%(v,self.vars[v]))
                    with open("%s/env.csh"%installdir,"a") as f:
                        f.write("setenv %s \"%s\""%(v,self.vars[v]))

        if "clone" in self.vars:
            for repo in self.vars['clone']:
                if not exe("rmdir %s && git clone %s %s"%(srcdir,repo,srcdir)):
                    return False

        if "tarball" in self.vars:
            for url in self.vars['tarball']:
                response = requests.get(url,stream=True)
                if response.status_code == 200:
                    tar = tarfile.open(fileobj=response.raw,mode="r|*")
                    tar.extractall(srcdir)
                    print os.listdir(srcdir)
                    if len(os.listdir(srcdir)) == 1:
                        exe("mv %s/%s/* %s/"%(srcdir,os.listdir(srcdir)[0],srcdir))


        if "preexec" in self.vars:
            for cmd in self.vars['preexec']:
                exe("cd %s && %s"%(srcdir,cmd))

        if "installsrc" in self.vars:
            for f in self.vars['installsrc']:
                shutil.move("%s/%s"%(srcdir,f),installdir)

    def link(self,installdir,linkdir):
        exe("mkdir -p %s/etc/env"%(linkdir))
        exe("ln -s %s/env.sh %s/etc/env/%s.sh"%(installdir,linkdir,self.name))
        exe("ln -s %s/env.csh %s/etc/env/%s.csh"%(installdir,linkdir,self.name))
        for p in self.vars['linkpaths']:
            exe("mkdir -p %s/%s"%(linkdir,p))
            try:
                for f in os.listdir("%s/%s"%(installdir,p)):
                    logging.debug("linking %s"%f)
                    fname = os.path.basename(f)
                    if os.path.isfile("%s/%s/%s"%(linkdir,p,fname)):
                        logging.warning("%s already exists in %s/%s"%(fname,linkdir,p))
                        logging.warning("Maybe this package is already linked as a different version? Try psrsoft relink %s"%(self.name))
                        self.unlink(installdir,linkdir)
                        return False
                    exe("ln -s %s/%s/%s %s/%s/%s"%(installdir,p,f,linkdir,p,fname))
            except IOError as e:
                logging.warning(e)
        for fr,to in self.xlinks:
            logging.debug("linking %s => %s"%(fr,to))
            exe("mkdir -p %s/%s"%(linkdir,os.path.dirname(to)))
            exe("ln -s %s/%s %s/%s"%(installdir,fr,linkdir,to))
        return True


    def unlink(self,installdir,linkdir):
        matchpath = os.path.abspath(linkdir)+'/'
        logging.debug("unlinking from %s"%matchpath)
        for root, dirnames, filenames in os.walk(matchpath, followlinks=False):
            for fname in filenames+dirnames:
                linkname=os.path.join(root, fname)
                if os.path.islink(linkname):
                    tgt = os.path.abspath(os.readlink(linkname))
                    tgt.startswith(matchpath)
                    logging.debug("unlink %s"%linkname)
                    os.unlink(linkname)



    def getdeps(self, pkgcache, use, installed=[]):
        requires = list(self.requires)

        for u in use:
            if u in usingclauses:
                requires.append(u.requires)
        deps = list()
        for r in list(requires):
            for p in installed:
                if r.compare(p.tag):
                    requires.remove(r)
                    break
            for p in pkgcache:
                if r.compare(p.tag):
                    deps.append(p)
                    requires.remove(r)
                    break
        for d in list(deps):
            deps.append(d.getdeps(pkgcache,use,deps))
        for r in requires:
            # left over entries are cache misses
            deps.append(missingpkg(r))
        return deps





    def parseline(self,line):

        e = line.split("#")
        if len(e) < 1:
            return False
        line2=e[0]
        if line2==line2.lstrip():
            self.currentclause=None
        nic = (self.currentclause == None)
        if nic:
            cobj=self
        else:
            cobj=self.currentclause
        e = line2.split()
        if len(e) < 1:
            return False


        match = self.kvregex.match(line)
        if match:
            g= match.groups()
            var=g[2]
            if (var[0]=='"' and var[-1]=='"') or (var[0]=="'" and var[-1]=="'"):
                var = var[1:-1]

            if g[1]=="+=" and g[0] in cobj.vars:
                cobj.vars[g[0]].append(var)
            else:
                cobj.vars[g[0]] = [var]
            return True


        key = e[0].lower().strip()
        rest=line2[len(key)+1:].strip()

        if key=="package" and nic:
            self.name=rest
            return True
        if key=="version" and nic:
            self.version=rest
            self.tag = tag("%s = %s"%(self.name,rest))
            return True
        if key=="type" and nic:
            self.pkgtype=rest
            return True
        if key=="requires":
            cobj.requires.append(tag(rest))
            return True
        if key=="link":
            cobj.xlinks.append((e[1],e[2]))
            return True

        if key=="using" and nic:
            self.currentclause = usingclause(e[1])
            if len(e) > 2:
                self.currentclause.desc=' '.join(e[2:])
            self.usingclauses[e[1]] = self.currentclause
            return True

        if nic:
            self.sparelines.append(line)
        else:
            self.currentclause.sparelines.append(line)

    @classmethod
    def parse(cls,f):
        obj = cls()
        for line in f:
            obj.parseline(line)

        if obj.pkgtype == "basic":
            return obj
        else:
            # Detect the correct object type
            if obj.pkgtype in cls.types:
                return cls.types[obj.pkgtype](obj)
            else:
                logging.error("Unknown package type %s (%s)"%(obj.name,obj.pkgtype))
                return None

class missingpkg(package):
    def __init__(self,t):
        super(package,self).__init__()
        self.pkgtype="missing"
        self.version=t
    def __repr__(self):
        return "MISSING PKG: %s"%(self.version)


