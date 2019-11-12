import re
try:
    import readline
except:
    pass
import urllib2
import json
import ssl
import os
import datetime
import itertools
#import trace
#import pdb
import random
import threading
import Queue
from collections import namedtuple
import interfaces.switchpreviewutil as switchpreviewutil
from localutils.custom_utils import *
import logging

# Create a custom logger
# Allows logging to state detailed info such as module where code is running and 
# specifiy logging levels for file vs console.  Set default level to DEBUG to allow more
# grainular logging levels
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define logging handler for file and console logging.  Console logging can be desplayed during
# program run time, similar to print.  Program can display or write to log file if more debug 
# info needed.  DEBUG is lowest and will display all logging messages in program.  
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.CRITICAL)
f_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers.  This creates custom logging format such as timestamp,
# module running, function, debug level, and custom text info (message) like print.
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the parent custom logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)


def interface_menu():
    while True:
        print("\nSelect type of interface(s): \n\n" + \
          "\t1.) PC Interfaces: \n" + \
          "\t2.) VPC Interfaces: \n")
        selection = custom_raw_input("Select number: ")
        print('\r')
        if selection.isdigit() and selection != '' and 1 <= int(selection) <= 3:
            break
        else:
            continue
    return selection 

class pcAggrIf():
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def main(import_apic,import_cookie):
    while True:
        global apic
        global cookie
        cookie = import_cookie
        apic = import_apic
        allpclist = get_All_PCs(apic,cookie)
        allvpclist = get_All_vPCs(apic,cookie)
        clear_screen()
        location_banner('Show port-channel locations')

        selection = interface_menu()
        if selection == '1':
            interfacelist = port_channel_selection(allpclist)
            url = """https://{apic}/api/class/pcAggrIf.json?query-target-filter=eq(pcAggrIf.name,"{pcname}")&rsp-subtree=full&rsp-subtree-class=pcRsMbrIfs""".format(apic=apic,pcname=interfacelist[0].name)
            result = GetResponseData(url, cookie)
            for pcaggrif in result:
                print(pcaggrif['pcAggrIf']['attributes']['dn'])
                if pcaggrif['pcAggrIf']['children']:
                    for child in pcaggrif['pcAggrIf']['children']:
                        print('\t' + child['pcRsMbrIfs']['attributes']['tDn'])
            custom_raw_input('Press enter...')
        elif selection == '2':
            interfacelist = port_channel_selection(allvpclist)
               #     remove_per_interface(interfacelist, apic, cookie)
            #url = """https://{apic}/api/class/pcAggrIf.json?query-target-filter=eq(pcAggrIf.name,"{pcname}")&rsp-subtree=full&rsp-subtree-class=pcRsMbrIfs""".format(apic=apic,pcname=interfacelist[0].name)
            #result = GetResponseData(url, cookie)
            nodelocation, interfacelist = port_channel_location(interfacelist[0].name,apic,cookie)
            print(nodelocation, interfacelist)
            import pdb; pdb.set_trace()



#url = """https://{apic}/api/class/pcAggrIf.json?query-target-filter=eq(pcAggrIf.name,"{pcname}")&rsp-subtree=full&rsp-subtree-class=pcRsMbrIfs"""