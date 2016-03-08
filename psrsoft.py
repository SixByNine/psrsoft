#!/usr/bin/env python2

import sys
import os
import logging
import argparse

if __name__=="__main__":
    logging.basicConfig(format="%(levelname)s: %(msg)s",level=logging.INFO)
    logging.debug("python version %s"%sys.version_info)


    parser=argparse.ArgumentParser(description="Install and configure pulsar software.")

    parser.add_argument("-v","--debug",action='store_true',help="Activate verbose logging")
    parser.add_argument("-u","--update",action='store_true',help="Update psrsoft and repos before taking any action")
    parser.add_argument("-I","--interactive",action='store_true',help="Interactive installation")
    parser.add_argument("-c",action='store',help="Use specified config file",default=None,metavar="FILE.cfg")


    parser.add_argument("cmd",action='store',help="One of %(choices)s",choices=["install","update","remove","info"],metavar="action")
    
    
    parser.add_argument("pkg",action='store',nargs='*',help="Package to install")


    args = parser.parse_args()

    if args.debug:
        print "***VERBOSE MODE ENABLED***"
        logging.getLogger().setLevel(logging.DEBUG)

    args.cfg=args.c

    psrsoft_dir=os.environ.get('PSRSOFT_DIR')
    if psrsoft_dir==None:
        try:
            logging.debug("searching for psrsoft_dir")
            my_path = os.path.realpath(__file__)
            psrsoft_dir=os.path.dirname(my_path)
        except Exception as e:
            logging.error("Could not determine psrsoft path, please set $PSRSOFT_DIR to the root of the psrsoft install")
            raise e

    logging.debug("psrsoft_dir = %s"%psrsoft_dir)

    if args.cfg==None:
        args.cfg = "%s/psrsoft.cfg"%psrsoft_dir

    
    sys.path.append("%s/lib/requests"%psrsoft_dir)
    sys.path.append("%s/lib"%psrsoft_dir)
    import psrsoft_core as psrsoft

    cfg = psrsoft.config(args.cfg)
    psrsoft_url=cfg['url']

    oldv=psrsoft.__version__
    logging.debug("Psrsoft version: %s"%psrsoft.__version__)

    logging.debug("Command was %s"%args.cmd)
    if args.update or args.cmd=="update":
        logging.debug("Check for update")
        if not psrsoft.exe("cd %(path)s && git pull --rebase %(url)s master"%{'path':psrsoft_dir,'url':psrsoft_url}):
            logging.warning("Could not get updates")

    reload(psrsoft)
    logging.debug("Psrsoft version: %s"%psrsoft.__version__)
    if oldv != psrsoft.__version__:
        logging.debug("Reload config file with new version")
        cfg = psrsoft.config(args.cfg)

    got_requests=False
    try:
        import requests
        got_requests=True
    except ImportError as e:
        pass

    if not got_requests:
        logging.warning("Could not find requests library... try to install")

        ret = os.system("git clone https://github.com/kennethreitz/requests.git %s/lib/requests"%psrsoft_dir)
        if ret!=0:
            logging.error("Could not download requests library from github")
        else:
            print "Please re-run your psrsoft command"
        sys.exit(0)


    logging.debug("Found requests http library %s"%requests.__version__)

    logging.debug("Good to go... starting psrsoft")

    engine = psrsoft.psrsoft(args)
    engine.run()
