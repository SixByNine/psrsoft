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
        self.pkgtypes=dict()
        self.pkgtypes["automake"] = psrsoft_automake.package
        logging.debug("PkgTypes: "+", ".join(self.pkgtypes.keys()))
        p=package()
        p.parse(open("packages/tempo2/tempo2-repo.install"))
        p2 = psrsoft_automake.package(p)
        print p,p2

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


class package(object):
    def __init__(self):
        self.dependancies=dict()
        self.options=dict()
        self.pkgtype="none"
        self.sparelines = list()

    def parseline(self,line):
        e = line.split("#")
        if len(e) < 1:
            return False
        line2=e[0]
        e = line2.split()
        if len(e) < 1:
            return False
        key = e[0].lower().strip()
        rest=line2[len(key)+1:].strip()
        if key=="package":
            self.name=rest
            return True
        if key=="version":
            self.version=rest
            return True
        if key=="installer":
            self.pkgtype=rest
            return True
        self.sparelines.append(line)

    def parse(self,f):
        for line in f:
            self.parseline(line)

