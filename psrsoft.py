#!/usr/bin/env python2

import sys
import os
import logging
import argparse




def exe(cmd):
    logging.debug("Exec '%s'"%cmd)
    ret=os.system(cmd)
    if ret==0:
        return True
    else:
        logging.warning("Command failed: %s"%cmd)
        return False

if __name__=="__main__":
    logging.basicConfig(format="%(levelname)s: %(msg)s",level=logging.INFO)
    logging.debug("python version %s"%sys.version_info)


    parser=argparse.ArgumentParser(description="Install and configure pulsar software.")

    parser.add_argument("-v","--debug",action='store_true',help="Activate verbose logging")
    parser.add_argument("-u","--update",action='store_true',help="Update psrsoft and repos before taking any action")
    parser.add_argument("-I","--interactive",action='store_true',help="Interactive installation")
    parser.add_argument("--psrsoft-path",action='store',help="Manual set psrsoft path")
    parser.add_argument("--psrsoft-url",action='store',help="Manual set psrsoft url")
    parser.add_argument("--install-path",action='store',help="Manual set install root")


    parser.add_argument("cmd",action='store',help="One of %(choices)s",choices=["install","update","remove","info"],metavar="action")
    
    
    parser.add_argument("pkg",action='store',nargs='*',help="Package to install")


    args = parser.parse_args()

    if args.debug:
        print "***VERBOSE MODE ENABLED***"
        logging.getLogger().setLevel(logging.DEBUG)

    if args.psrsoft_path==None:
        try:
            logging.debug("searching for psrsoft_path")
            my_path = os.path.realpath(__file__)
            args.psrsoft_path=os.path.dirname(my_path)
        except Exception as e:
            logging.error("Could not determine psrsoft path, have to set on command line")
            raise e

    psrsoft_path=args.psrsoft_path
    logging.debug("psrsoft_path = %s"%psrsoft_path)

    if args.psrsoft_url==None:
        args.psrsoft_url="https://github.com/SixByNine/psrsoft.git"
    psrsoft_url=args.psrsoft_url


    logging.debug("Command was %s"%args.cmd)
    if args.update or args.cmd=="update":
        logging.debug("Check for update")
        if not exe("cd %(path)s && git pull --rebase %(url)s master"%{'path':psrsoft_path,'url':psrsoft_url}):
            logging.warning("Could not get updates")

    sys.path.append("%s/lib/requests"%psrsoft_path)
    sys.path.append("%s/lib"%psrsoft_path)
    import psrsoft_core as psrsoft
    logging.debug("Psrsoft version: %s"%psrsoft.__version__)

    got_requests=False
    try:
        import requests
        got_requests=True
    except ImportError as e:
        pass

    if not got_requests:
        logging.warning("Could not find requests library... try to install")

        ret = os.system("git clone https://github.com/kennethreitz/requests.git %s/lib/requests"%psrsoft_path)
        if ret!=0:
            logging.error("Could not download requests library from github")
        else:
            print "Please re-run your psrsoft command"
        sys.exit(0)


    logging.debug("Found requests http library %s"%requests.__version__)

    logging.debug("Good to go... starting psrsoft")

    engine = psrsoft.psrsoft(args)
