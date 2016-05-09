#automake installer for psrsoft
import psrsoft_core as core

class package(core.package):
    def __init__(self):
        super(package,self).__init__()
        self.pkgtype="automake"

    def __init__(self,generic):
        self.__dict__ = generic.__dict__.copy()
        self.pkgtype="automake"
        for line in self.sparelines:
            self.parseline(line)
    def parseline(self,line):
        print line.rstrip()
