import sys
import os
import logging
import argparse


__version__="2.0.0"

class psrsoft(object):
    def __init__(self,args):
        self.args=args

    def run(self):
        import psrsoft_automake
        package.types["automake"] = psrsoft_automake.package
        logging.debug("PkgTypes: "+", ".join(package.types.keys()))
        pkg = package.parse(open("packages/tempo2/tempo2-repo.install"))
        print pkg

class config(dict):
    def __init__(self,fname):
        self.desc = dict()
        self.desc['url'] = "Git URL for updating psrsoft."
        self['url']="https://github.com/SixByNine/psrsoft.git"

        self.reload(fname)

    def reload(self,fname):
        try:
            with open(fname) as infile:
                for line in infile:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    split = line.split("=",1)
                    key=split[0].lower().strip()
                    val=split[-1].strip("'\" ").strip()
                    self[key] = val
        except IOError as e:
            logging.warning("Could not read config file '%s'"%fname)
            print "Do you want to try to create a new config file?"
            yn = raw_input("(y/n): ").strip()
            if yn.lower()=="y" or yn=="":
                print "Creating config file, '%s'"%fname
                try:
                    with open(fname,"w") as ofile:
                        for key in self.keys():
                            if key in self.desc:
                                ofile.write("# %s\n"%(self.desc[key]))
                            ofile.write("# %s = %s\n\n"%(key.upper(),self[key]))
                    ofile.close()
                    exe("$EDITOR %s"%fname)
                    self.reload(fname)
                except Error as e:
                    logging.error("Error creating file")
                    raise e

            else:
                logging.warning("Continuing with default configuration")


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

    def __init__(self,name,version):
        self.name=name
        self.version=version

    def compare(self,other):
        if not other.name==self.name:
            return False
        if self.version=="" or other.version=="":
            return True
        vt1,vv1 = other.splitversion(other.version)
        vt2,vv2 = self.splitversion(self.version)

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


    def splitversion(self,verstring):
        e = verstring.split()
        if len(e)==1 or e[0]=="=":
            return tag.EQUAL,e
        if e[0]==">=":
            return tag.GEQ,e[1]
        if e[0]=="<=":
            return tag.LEQ,e[1]

    def __repr__(self):
        return "%s %s"%(self.name,self.version)


class usingclause(object):
    def __init__(self,name):
        self.name=name
        self.requires=list()
        self.vars=dict()
        self.desc=""
        self.sparelines=list()

    def __repr__(self):
        return "%s [%s]"%(self.name,self.desc)

class package(object):
    types=dict()

    def __init__(self):
        self.dependancies=dict()
        self.pkgtype="none"
        self.sparelines = list()

        self.requires = list()
        self.usingclauses = dict()
        self.vars = dict()
        self.currentclause=None

    def parseline(self,line):
        e = line.split("#")
        if len(e) < 1:
            return False
        line2=e[0]
        if line2==line2.lstrip():
            self.currentclause=None
        nic = (self.currentclause == None)
        e = line2.split()
        if len(e) < 1:
            return False
        key = e[0].lower().strip()
        rest=line2[len(key)+1:].strip()
        if key=="package" and nic:
            self.name=rest
            return True
        if key=="version" and nic:
            self.version=rest
            self.tag = tag(self.name,self.version)
            return True
        if key=="installer" and nic:
            self.pkgtype=rest
            return True
        if key=="requires":
            e = rest.split()
            if nic:
                self.requires.append(tag(e[0]," ".join(e[1:])))
            else:
                self.currentclause.requires.append(tag(e[0]," ".join(e[1:])))
            return True
        if len(e) > 2 and e[1] == "+=" or e[1] =="=":
            val = ' '.join(e[2:])
            if not key in self.vars or e[1]=="+=":
                self.vars[key] = [val]
            else:
                self.vars[key].append(val)
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

        # Detect the correct object type
        if obj.pkgtype in cls.types:
            return cls.types[obj.pkgtype](obj)
        else:
            return None
