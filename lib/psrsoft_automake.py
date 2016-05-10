#automake installer for psrsoft
import psrsoft_core as core
import logging

class package(core.package):
    def __init__(self):
        super(package,self).__init__()
        self.pkgtype="automake"

    def __init__(self,generic):
        self.__dict__ = generic.__dict__.copy()
        self.pkgtype="automake"
        if not 'makeflags' in self.vars:
            self.vars['makeflags']=[]

        if not 'installflags' in self.vars:
            self.vars['installflags']=['install']

        if not 'configureopts' in self.vars:
            self.vars['configureopts']=[]

        for line in self.sparelines:
            self.parseline(line)

    def parseline(self,line):
        print line.rstrip()

    def build(self, installdir, builddir, srcdir):
        super(package,self).build(installdir,builddir,srcdir)
        logging.debug("begin automake-style package install")
        core.exe("cd %s && %s/configure --prefix=%s %s"%(builddir,srcdir,installdir," ".join(self.vars['configureopts'])))
        core.exe("cd %s && $make %s"%(builddir, " ".join(self.vars['makeflags'])))
        core.exe("cd %s && $make %s"%(builddir, " ".join(self.vars['installflags'])))

    def link(self,installdir, linkdir):
        super(package,self).link(installdir, linkdir)

    def unlink(self, installdir, linkdir):
        super(package,self).unlink(installdir, linkdir)
