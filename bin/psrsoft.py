#!/usr/bin/python
import sys,os,re,random;

quiet_flag = ""
quiet_mode = ""
quiet_wget = ""
psrsoft_dir = os.environ['PSRSOFT_DIR']
psrsoft_usr = os.environ['PSRSOFT_USR']
pkg_idx_ext = os.environ['PSRSOFT_TREE']

def help():
    print "psrsoft-install package-name {options}"
    print ""
    print "--search\tdo a grep for package-name"
    print "--stable\tinstall the latest stable version"
    print "--testing\tinstall the latest testing version"
    print "--devel\tTry and get CVS version"
    print "--quiet\tReduce output"
    print "--quieter\tReduce output even more"
    print "--rebuild\tRemake dependancies even if they are up-to-date"
    print "--no-[pkg]\tBuild without optional package pkg"
    print "--uninstall\tRemove package: Be careful of depenancies!"
    print "--virtual\tDon't actualy install, just mark package as installed"
    print "--clear-cache\tremove cached package install files"
    print "--old\tDon't update the package index (updated by default)"
    print "--selfupdate\tUpdate the psrsoft software then exit"
    print ""
    print "Special Packages:"
    print "world\t All installed packages"
    print "dirty\t Packages who's dependancies have been updated since install"
    sys.exit(1)



class counter:
    def __init__(self):
        self.count=0

    def next(self):
        self.count+=1
        return self.count


def check_dirty(dirty_pkg):
    if len(dirty_pkg) > 0:
        print "Warning... there are some 'dirty' packages on your system..."

        i=0
        for pkg in dirty_pkg:
            i=i+1
            print "% 3d % 15s |[33mD [0m| Dirty, needs to be rebuilt"%(i,pkg)
        print "\nThey should be rebuilt so that they use the newly installed code"
        print ""
        ex=os.path.dirname(sys.argv[0])
        print "Try:\n $ %s/psrsoft dirty"%ex
        print "to update all dirty packages"


def read_pkg_idx(pkg_index):
    file=open(pkg_index)
    pkgs=dict()
    for line in file:
        elems=line.split();
        if len(elems) > 3:
            pkgs[elems[0]] = dict(name=elems[0], version=elems[1], date=elems[2], url=elems[3])
    file.close()
    return pkgs


def save_pkg_idx(curr_pkg,name):
    file=open(psrsoft_usr+"/var/psrsoft/%s.tmp"%(name),"w")
    for key in curr_pkg:
        file.write("%s %s %s %s\n"%(curr_pkg[key]['name'],curr_pkg[key]['version'],curr_pkg[key]['date'],curr_pkg[key]['url']))
    file.close()
    os.system("mv %s/var/psrsoft/%s.pkg %s/var/psrsoft/%s.bak"%(psrsoft_usr,name,psrsoft_usr,name))
    os.system("mv %s/var/psrsoft/%s.tmp %s/var/psrsoft/%s.pkg"%(psrsoft_usr,name,psrsoft_usr,name))


def fmt_date(date):
    if date=="":
        return ""
    else:
        return "%s-%s-%s %s:%s"%(date[0:4],date[4:6], date[6:8],date[8:10],date[10:12])


def get_depenancies(pkg,pkg_idx=dict(),curr_pkg=dict(),optional=0,opt_out=list(),ucount=counter()):

    os.chdir(psrsoft_dir+"/pkg_files")
    #print "wget --no-cache %s -qN %s"%(quiet_wget,pkg['url'])
    os.system("wget --no-cache %s  -qN %s"%(quiet_wget,pkg['url']))

    install_file = open(os.path.basename(pkg['url']))

    to_install=list()

    if pkg['name'] in curr_pkg:
        pkg['replace']=curr_pkg[pkg['name']]
        pkg['repldir']=int(pkg['date']) - int(pkg['replace']['date']);

    pkg=pkg.copy()

    pkg['uid']=ucount.next()
    pkg['opt']=optional
    to_install.append(pkg)
    for line in install_file:
        line = line.strip()
        if line.startswith("#"):
            continue
        elems = line.split()
        if len(elems) < 1:
            continue

        keyword=elems[0]
        if keyword=="DEPENDS" or keyword=="RECOMMENDS":
            opt=optional
            if keyword=="RECOMMENDS":
                opt=optional+1
            replace=0
            date="0"
            name=elems[1]
            if name in opt_out and keyword=="RECOMMENDS":
                to_install.append(dict(name=name,opt=-1,uid=ucount.next()))
                continue
            if (len(elems) > 2):
                date=elems[2]
            if date=="latest":
                if name in pkg_idx:
                    date=pkg_idx[name]['date']
                else:
                    to_install.append(dict(name=name,err="not found (no recent versions)"))
                    continue
            if name not in pkg_idx:
                # the package is not in the index!
                to_install.append(dict(name=name,err="not found"))
                continue
            if int(pkg_idx[name]['date']) >= int(date):
                to_install.extend(get_depenancies(pkg_idx[name],pkg_idx,curr_pkg,opt,opt_out,ucount))
                continue
            else:
                to_install.append(dict(name=name,err="out of date"))
                continue
        if keyword=="WARNING":
            if "warning" not in pkg:
                pkg['warning']=list()
            str=""
            for s in elems[1:]:
                str+=" "+s
            pkg['warning'].append(str)
    install_file.close()
    return to_install

def install_pkg(curr_pkg,dirty_pkg,pkg):
    os.chdir(psrsoft_dir+"/pkg_files")
    install_file = open(os.path.basename(pkg['url']))
    url=""
    remove=list()
    rm=list()
    for line in install_file:
        line = line.strip()
        if line.startswith("#"):
            continue
        elems = line.split()
        if len(elems) < 1:
            continue

        keyword=elems[0]

        if keyword=="URL":
            url=elems[1]
        if keyword=="REPLACES":
            remove.append(elems[1])
        if keyword=="RM":
            rm.append(elems[1])

    install_file.close()

    for p in remove:
        remove_pkg(curr_pkg,dirty_pkg,p)

    for path in rm:
        print "Clean up: rm -rf %s/%s"%(psrsoft_usr,path)
        os.system("rm -vrf %s/%s"%(psrsoft_usr,path))

    if url=="":
        print "Install file %s does not specify a URL"%os.path.basename(pkg['url'])
        sys.exit(3)

    print "wget --no-cache %s -N %s"%(quiet_wget,url)
    ret = os.system("wget --no-cache %s -N %s"%(quiet_wget,url))
    if ret!=0:
        print "Could not fetch tarball"
        sys.exit(3)
    print "Un-taring package tarball"
    os.system("mkdir -p %s"%psrsoft_usr)
    verb=""
    if quiet_mode=="":
        verb="-v"
    ret = os.system("tar %s -xzf %s -C %s"%(verb,os.path.basename(url),psrsoft_usr))
    if ret!=0:
        print "Could not extract tarball"
        sys.exit(3)

    print "Running install scripts"
    os.chdir(psrsoft_usr)
    cmd="/bin/bash -v ./var/psrsoft/installers/%s"%(pkg['name'])
    print cmd
    ret=os.system(cmd)
    if ret!=0:
        print "Build script failed!"
        sys.exit(3)
    curr_pkg[pkg['name']]=pkg
    save_pkg_idx(curr_pkg,"installed")

    # find dirtied packages...
    print "Checking for dirtied packages"
    for cpkg in curr_pkg:
        dep=get_depenancies(curr_pkg[cpkg],curr_pkg=curr_pkg)
        for dpkg in dep:
            if dpkg['name'] == pkg['name']:
                dirty_pkg[cpkg]=curr_pkg[cpkg]

    if pkg['name'] in dirty_pkg:
        del dirty_pkg[pkg['name']]
    save_pkg_idx(dirty_pkg,"dirty")

    print "Finished installing %s"%pkg['name']

def remove_pkg(curr_pkg,dirty_pkg,pkg_name):
    os.chdir(psrsoft_usr)
    cmd="/bin/bash -v ./var/psrsoft/uninstallers/%s"%(pkg_name)
    print cmd
    os.system(cmd)
    if pkg_name in curr_pkg:
        pkg=curr_pkg[pkg_name]
        del curr_pkg[pkg_name]
        save_pkg_idx(curr_pkg,"installed")

        # find dirtied packages...
        print "Checking for dirtied packages"
        for cpkg in curr_pkg:
            dep=get_depenancies(curr_pkg[cpkg],curr_pkg=curr_pkg)
            for dpkg in dep:
                if dpkg['name'] == pkg['name']:
                    dirty_pkg[cpkg]=curr_pkg[cpkg]

        if pkg['name'] in dirty_pkg:
            del dirty_pkg[pkg['name']]
        save_pkg_idx(dirty_pkg,"dirty")


def main():
    quiet_flag = ""
    quiet_mode = ""
    quiet_wget = ""
    virtual=uninstall=0
    psrsoft_dir = os.environ['PSRSOFT_DIR']
    psrsoft_usr = os.environ['PSRSOFT_USR']
    pkg_idx_ext = os.environ['PSRSOFT_TREE']



    os.chdir(psrsoft_dir+"/pkg_files")
    if len(sys.argv) < 2:
        help()
        
    pkg_search = list()
    upgrade_only=1
    clear_cache=0
    yesyesyes=selfupdate=0
    updateidx=1
    ignore_dirty=make_dirty=search=0
    opt_out=list()
    for arg in sys.argv[1:]:
        if arg == "--help":
            help()
        if arg.startswith("--no-"):
            opt_out.append(arg[5:])
        if arg == "--uninstall":
            uninstall=1
        if arg == "--virtual":
            virtual=1
        if arg == "--search":
            search=1
        if arg == "--rebuild":
            upgrade_only=0
        if arg == "--upgrade":
            upgrade_only=1
        if arg == "--mark-dirty":
            make_dirty=1
        if arg == "--selfupdate":
            selfupdate=1
        if arg == "--yes":
            yesyesyes=1
        if arg == "--old":
            updateidx=0
        if arg == "--clear-cache":
            clear_cache=1
        if arg == "--ignore-dirty":
            ignore_dirty=1
        if arg == "--stable":
            pkg_idx_ext="stable"
        if arg == "--testing":
            pkg_idx_ext="testing"
        if arg == "--devel":
            pkg_idx_ext="devel"
        if arg =="--quiet":
            quiet_flag = '> /dev/null'
            quiet_mode="quietly"
        if arg =="--quieter":
            quiet_wget = "-q"
            quiet_flag = '>& /dev/null'
            quiet_mode = "very quietly"

        if not arg.startswith("-"):
            pkg_search.append(arg)


    print "==== PSRSOFT version 1.5 ===="
    if pkg_idx_ext=="stable":
        print " Pkg Index: '[32mstable[0m'"
    if pkg_idx_ext=="testing":
        print " Pkg Index: '[35mtesting[0m'"
    if pkg_idx_ext=="devel":
        print " Pkg Index: '[31mdevel[0m'"
    print "============================="

    if clear_cache:
        print "Clearing package install cache"
        cmd="rm -f "+psrsoft_dir+"/pkg_files/*"
        print cmd
        os.system(cmd)
        sys.exit(0)

    if updateidx:
        print "Updating package index"
        os.system(psrsoft_dir+"/bin/psrsoft-update-index");
    else:
        print "Using old package index (may be out of date!)"

    if selfupdate:
        print "Updating psrsoft software"
        os.system(psrsoft_dir+"/bin/psrsoft-selfupdate");
        sys.exit(0)


    curr_pkg=read_pkg_idx(psrsoft_usr+"/var/psrsoft/installed.pkg")
    dirty_pkg=read_pkg_idx(psrsoft_usr+"/var/psrsoft/dirty.pkg")

    pkg_index_file = "pkg_idx.%s"%(pkg_idx_ext)

    pkgs=read_pkg_idx(pkg_index_file)
    ipkg=list()

    if search==1 and len(pkg_search)==0:
        pkg_search.append(".*")

    if "world" in pkg_search:
        print "Re-building all installed packages"
        pkg_search.remove("world")
        for pkg in curr_pkg:
            pkg_search.append("^%s$"%pkg)

    if "dirty" in pkg_search:
        print "Re-building dirty packages..."
        pkg_search.remove("dirty")
        for pkg in dirty_pkg:
            pkg_search.append("^%s$"%pkg)


    for pkg_search_name in pkg_search:
        pkg_re = re.compile(pkg_search_name)
        pkg_choices = list()

        if uninstall:
            pkgs=curr_pkg
            print "Searching for package %s in installed packages"%(pkg_search_name)
        else:
            print "Searching for package %s in %s tree"%(pkg_search_name,pkg_idx_ext)
        i = 1
        for name in pkgs:
            if pkg_re.match(name):
                pkg = pkgs[name]
                print "%d) %s %s"%(i,pkg['name'],pkg['version'])
                i+=1
                pkg_choices.append(pkg)


        if i == 1:
            print "No matching package found..."
            sys.exit(2)

        if search:
            sys.exit(0)

        choice=1
        choose=1
        if i > 2 and choose==1:
            print "Select package to install. (0 to exit)"
            choice = int(raw_input("(%d-%d) > "%(1,i-1)))

        if choice < 1 or choice > (i-1):
            print "Choice %d out of range... Exiting"%(choice)
            sys.exit(2)

        pkg=pkg_choices[choice-1]
        ipkg.append(pkg)
        if make_dirty:
            dirty_pkg[pkg['name']]=pkg


    if uninstall:
        for pkg in ipkg:
            try:
                choice = raw_input("Run uninstall script for %s? (y/n) "%pkg['name'])
            except KeyboardInterrupt:
                choice="n"
            if not choice.startswith("y"):
                print "Not uninstalling!"
                continue
            else:
                print "Uninstalling %s"%pkg['name']
                remove_pkg(curr_pkg,dirty_pkg,pkg['name'])

        check_dirty(dirty_pkg)
        sys.exit(0)
    if virtual:
        for pkg in ipkg:
            print "Marking %s (%s %s) as installed ([31mNO[0m installing done!!!)"%(pkg['name'],pkg['version'],fmt_date(pkg['date']))
            curr_pkg[pkg['name']] = pkg
            save_pkg_idx(curr_pkg,"installed")
        sys.exit(0)

    install_list=list()
    ipkg.reverse()
    print "\nAnalysing dependancies"
    for pkg in ipkg:
        install_list.extend(get_depenancies(pkg,pkgs,curr_pkg,opt_out=opt_out))

    name_list=list()
    rm_list=list()

    # We have to look for packages that would be compiled twice!
    # It's tricky as we want to make sure that packages are only
    # really optional if they are not required by any package
    install_list.reverse()
    for pkg in install_list:
        if 'opt' in pkg and (pkg['opt'] != -2 and pkg['name'] in name_list):
            for alt in install_list:
                if alt['name'] == pkg['name'] and alt['uid'] != pkg['uid'] and alt['opt'] != -2:
                    # we have the already installed pkg.
                    rm_list.append(pkg)
                    if pkg['opt'] == 0:
                        for k in pkg:
                            alt[k]=pkg[k]
                    pkg['opt']=-2
                    break

        else:
            name_list.append(pkg['name'])

    for pkg in rm_list:
        install_list.remove(pkg)



    print "\n\nPackages to be installed..."
    print     "===========================\n"
    i=1
    remove_list=list()
    for pkg in install_list:
        if 'err' in pkg:
            print "%s ERROR ---- %s"%(pkg['name'],pkg['err'])
            print "\n\nSorry there was a package that could not be installed"
            sys.exit(1)
        repl=""
        show=1
        repflag="[32mN"
        if 'replace' in pkg:
            repl=" replaces [%s %s]"%(pkg['replace']['version'],fmt_date(pkg['replace']['date']))
            if pkg['repldir'] == 0:
                if pkg['name'] in dirty_pkg and ignore_dirty==0:
                    repflag="[33mD"
                    repl="Dirty, may need rebuild"
                    rm = 0
                else:
                    repflag="[33mR"
                    rm = 1
                if upgrade_only:
                    # Don't remove packages if they were explicitly specified
                    # on the command line
                    for pp in ipkg:
                        if pkg['name'] == pp['name']:
                            rm=0
                    # if we are upgrading, and the package is a reinstall
                    # remove it from the list and don't show
                    if rm:
                        remove_list.append(pkg)
                        show=0
            elif pkg['repldir'] > 0:
                repflag="[36mU"
            elif pkg['repldir'] < 0:
                repflag="[31md"
        opt=pkg['opt']
        optflag=" "
        if opt > 0:
            optflag="[35mO"
        if opt == -1:
            optflag="[31mX"
            remove_list.append(pkg)
            pkg['date']=""
            pkg['version']="ignored by --no-"+pkg['name']
            repl=""
            if pkg['name'] in curr_pkg:
                pkg['replace']=curr_pkg[pkg['name']]
                optflag="[33m-"
                repl="Already installed [%s %s]"%(pkg['replace']['version'],fmt_date(pkg['replace']['date']))
            repflag=" "
        if show:
            print "% 3d % 15s |%s%s[0m| (%s %s) %s"%(i,pkg['name'],repflag,optflag,pkg['version'],fmt_date(pkg['date']),repl)
            i+=1

    for pkg in remove_list:
        install_list.remove(pkg)

    warns=0
    for pkg in install_list:
        if "warning" in pkg:
            print ""
            print "WARN(%s):"%pkg['name']
            for w in pkg['warning']:
                print "      %s"%w
            print ""
            warns += 1
        if 'repldir' in pkg and pkg['repldir'] < 0:
            print ""
            print "WARN(%s):"%pkg['name']
            print "      This is a downgrade in your current version!"
            warns += 1

    if warns > 0:
        print "There were some warnings, please read the above messages carefully before continuing."
    if yesyesyes:
        choice="y"
    else:
        try:
            choice = raw_input("Install %d packages into %s? (y/n)"%(i-1,psrsoft_usr))
        except KeyboardInterrupt:
            choice="n"

    if not choice.startswith("y"):
        print "Ok, aborting"
        sys.exit(0)
    print "Installing..."


    for pkg in install_list:
        print "]0;Installing %s\a"%pkg['name']
        install_pkg(curr_pkg,dirty_pkg,pkg)
        print "]0;Done %s\a"%pkg['name']

    check_dirty(dirty_pkg)

if __name__ == "__main__":
    main()
