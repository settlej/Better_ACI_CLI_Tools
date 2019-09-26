#!/bin//python
import re
try:
    import readline
except:
    pass
import urllib2
import json
import ssl
import os
import itertools
import threading
import Queue
from localutils.custom_utils import *
import logging

# Create a custom logger
# Allows logging to state detailed info such as module where code is running and 
# specifiy logging levels for file vs console.  Set default level to DEBUG to allow more
# grainular logging levels
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

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


class fabricPathEp(object):
    def __init__(self, descr=None, dn=None,name=None, number=None):
        self.name = name
        self.descr = descr
        self.dn = dn
        self.number = number
        self.leaf =  dn.split('/')[2].replace('paths','leaf')
        self.shortname = name.replace('eth1/','')
        self.removedint = '/'.join(dn.split('/')[:-2])
        if 'extpaths' in self.dn:
            self.fex = self.dn.split('/')[3].replace('extpaths','fex')
        else:
            self.fex = ''
    def __repr__(self):
        return self.dn
    def __getitem__(self, number):
        if number in self.dn:
            return self.dn
        else:
            return None

def grouper(iterable, n, fillvalue=''):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n  # creates list * n so args is a list of iters for iterable
    return itertools.izip_longest(*args, fillvalue=fillvalue)

class pcObject():
    def __init__(self, name=None, dn=None, number=None):
        self.name = name
        self.dn = dn
        self.number = number
    def __repr__(self):
        return self.dn
    def __get__(self, num):
        if num in self.number:
            return self.name
        else:
            return None

def parseandreturnsingelist(liststring, collectionlist):
    try:
        rangelist = []
        singlelist = []
        seperated_list = liststring.split(',')
        for x in seperated_list:
            if '-' in x:
                rangelist.append(x)
            else:
                singlelist.append(int(x))
        if len(rangelist) >= 1:
            for foundrange in rangelist:
                tempsplit = foundrange.split('-')
                for i in xrange(int(tempsplit[0]), int(tempsplit[1])+1):
                    singlelist.append(int(i))
   #     print(sorted(singlelist))
        if max(singlelist) > len(collectionlist) or min(singlelist) < 1:
            print('\n\x1b[1;37;41mInvalid format and/or range...Try again\x1b[0m\n')
            return 'invalid'
        return list(set(singlelist)) 
    except ValueError as v:
        print('\n\x1b[1;37;41mInvalid format and/or range...Try again\x1b[0m\n')
        return 'invalid'


def goodspacing(column):
    if column.fex:
        return column.leaf + ' ' + column.fex + ' ' + str(column.name)
    elif column.fex == '':
        return column.leaf + ' ' + str(column.name)

def physical_selection(all_leaflist, allepglist):
    nodelist = [node['fabricNode']['attributes']['id'] for node in all_leaflist]
    nodelist.sort()
    for num,node in enumerate(nodelist,1):
        print("{}.) {}".format(num,node))
    while True:
        #try:
            asknode = custom_raw_input('\nWhat leaf(s): ')
            print('\r')
            returnedlist = parseandreturnsingelist(asknode, nodelist)
            if returnedlist == 'invalid':
                continue
            chosenleafs = [nodelist[int(node)-1] for node in returnedlist]
            break
        #except KeyboardInterrupt as k:
        #    print('\n\nEnding Script....\n')
        #    return
    compoundedleafresult = []
    for leaf in chosenleafs:
        url = """https://{apic}/api/node/class/fabricPathEp.json?query-target-filter=and(not(wcard(fabricPathEp.dn,%22__ui_%22)),""" \
              """and(eq(fabricPathEp.lagT,"not-aggregated"),eq(fabricPathEp.pathT,"leaf"),wcard(fabricPathEp.dn,"topology/pod-1/paths-{leaf}/"),""" \
              """not(or(wcard(fabricPathEp.name,"^tunnel"),wcard(fabricPathEp.name,"^vfc")))))&order-by=fabricPathEp.dn|desc""".format(leaf=leaf,apic=apic)
        result = GetResponseData(url, cookie)
        compoundedleafresult.append(result)
    result = compoundedleafresult
    interfacelist = []
    interfacelist2 = []
    for x in result:
        for pathep in x:
            dn = pathep['fabricPathEp']['attributes']['dn']
            name = pathep['fabricPathEp']['attributes']['name']
            descr = pathep['fabricPathEp']['attributes']['descr']
            if 'extpaths' in dn:
                interfacelist2.append(fabricPathEp(descr=descr, dn=dn ,name=name))
            else:
                interfacelist.append(fabricPathEp(descr=descr, dn=dn ,name=name))
            
    interfacelist2 = sorted(interfacelist2, key=lambda x: (x.fex, int(x.shortname)))
    interfacelist = sorted(interfacelist, key=lambda x: int(x.shortname))
    interfacenewlist = interfacelist2 + interfacelist
    interfacelist = []
    interfacelist2 = []
    finalsortedinterfacelist = sorted(interfacenewlist, key=lambda x: x.removedint)
    interfacedict = {}
    for num,interf in enumerate(finalsortedinterfacelist,1):
        if interf != '':
           interfacedict[interf] = str(num) + '.) '
           interf.number = num
    listlen = len(finalsortedinterfacelist) / 3
    firstgrouped = [x for x in grouper(finalsortedinterfacelist,listlen)]
    finalgrouped = zip(*firstgrouped)
    for column in finalgrouped:
        a = column[0].number
        b = goodspacing(column[0]) + '  ' + column[0].descr[:25]
        c = column[1].number
        d = goodspacing(column[1]) + '  ' + column[1].descr[:25]
        if column[2] == '' or column[2] == None:
            e = ''
            f = ''
        else:
            #e = interfacedict[column[2]]
            e = column[2].number
            f = goodspacing(column[2])
            #f = row[2].leaf + ' ' + row[2].fex + ' ' + str(row[2].name)
        print('{:6}.) {:45}{}.) {:45}{}.) {}'.format(a,b,c,d,e,f))
    while True:
        #try:
            selectedinterfaces = custom_raw_input("\nSelect interface(s) by number: ")
            print('\r')
            if selectedinterfaces.strip().lstrip() == '':
                continue
            intsinglelist = parseandreturnsingelist(selectedinterfaces,finalsortedinterfacelist)
            if intsinglelist == 'invalid':
                continue
            choseninterfaceobjectlist = filter(lambda x: x.number in intsinglelist, finalsortedinterfacelist)
           # for number in intsinglelist:
           #     if not (0 < int(number) <= len(finalsortedinterfacelist)):
           #         print('here')
           #         print("\n\x1b[1;37;41mInvalid format and/or range...Try again\x1b[0m\n")
           #         continue
            break
        #except KeyboardInterrupt as k:
        #    print('\n\nEnding Script....\n')
        #    exit()
    return choseninterfaceobjectlist

      #  except Exception as e:

def shutinterfaces(interfaces):
    queue = Queue.Queue()
    interfacelist = []
    interfacelist2 =[]
    for interface in interfaces:
        t = threading.Thread(target=postshut, args=(interface,queue,))
        t.start()
        interfacelist.append(t)
    for t in interfacelist:
        t.join()
        interfacelist2.append(queue.get())
    for x in sorted(interfacelist2):
        print(x)

def postshut(interface,queue):
        url = 'https://{apic}/api/node/mo/uni/fabric/outofsvc.json'.format(apic=apic)
        # data is the 'POST' data sent in the REST call to 'blacklist' (shutdown) on a normal interface
        data = """'{{"fabricRsOosPath":{{"attributes":{{"tDn":"{interface}","lc":"blacklist"}},"children":[]}}}}'""".format(interface=interface)
        result, error =  PostandGetResponseData(url, data, cookie)
        if result == []:
            queue.put('[Complete] shut ' + interface.name)

def noshutinterfaces(interfaces):
    queue = Queue.Queue()
    interfacelist = []
    interfacelist2 =[]
    for interface in interfaces:
        t = threading.Thread(target=postnoshut, args=(interface,queue,))
        t.start()
        interfacelist.append(t)
    for t in interfacelist:
        t.join()
        interfacelist2.append(queue.get())
    for x in sorted(interfacelist2):
        print(x)

def postnoshut(interface,queue):
        url = 'https://{apic}/api/node/mo/uni/fabric/outofsvc.json'.format(apic=apic)
        # data is the 'POST' data sent in the REST call to delete object from 'blacklist' (no shut)
        data = """'{{"fabricRsOosPath":{{"attributes":{{"dn":"uni/fabric/outofsvc/rsoosPath-[{interface}]","status":"deleted"}},"children":[]}}}}'""".format(interface=interface)
        result, error =  PostandGetResponseData(url, data, cookie)
        if result == []:
            queue.put('[Complete] no shut ' + interface.name)

def port_channel_selection(allpclist,allepglist):
    pcobjectlist = []
    for pc in allpclist:
        pcobjectlist.append(pcObject(name = pc['fabricPathEp']['attributes']['name'],
                                     dn = pc['fabricPathEp']['attributes']['dn'] ))
    print("\n{:>4} |  {}".format("#","Port-Channel Name"))
    print("-"* 65)
    for num,pc in enumerate(sorted(pcobjectlist, key=lambda x: x.name),1):
        print("{:>4}.) {}".format(num,pc.name))
        pc.number = num
    while True:
        try:
            askpcnum = custom_raw_input("\nWhich number(s)?: ")
            print('\r')
            if askpcnum.strip().lstrip() == '':
                continue
            pcsinglelist = parseandreturnsingelist(askpcnum,pcobjectlist)
            if pcsinglelist == 'invalid':
                continue
            choseninterfaceobjectlist = filter(lambda x: x.number in pcsinglelist, pcobjectlist)
            break
        except ValueError:
            print("\n\x1b[1;37;41mInvalid format and/or range...Try again\x1b[0m\n")
    return choseninterfaceobjectlist


def main(import_apic, import_cookie):
    while True:
        #get_Cookie()
        global apic
        global cookie
        cookie = import_cookie
        apic = import_apic
        allepglist = get_All_EGPs(apic,cookie)
        allpclist = get_All_PCs(apic,cookie)
        allvpclist = get_All_vPCs(apic,cookie)
        all_leaflist = get_All_leafs(apic,cookie)
    
        selection = interface_menu()
    
        if selection == '1':
            interfaces = physical_selection(all_leaflist, allepglist)
            #print(interfaces)
            print('\r')
            while True:
                option = custom_raw_input(("Would you like to do?\n\
                        \n1.) shut\
                        \n2.) no shut\
                        \n3.) bounce \n\
                        \nSelect a number: "))
                if option == '1':
                    print('\n')
                    shutinterfaces(interfaces)
                    break
                elif option == '2':
                    print('\n')
                    noshutinterfaces(interfaces)
                    break
                elif option == '3':
                    print('\n')
                    shutinterfaces(interfaces)
                    noshutinterfaces(interfaces)
                    break
                else:
                    print('\n\x1b[1;31;40mInvalid option, please try again...\x1b[0m\n')
                    continue
            custom_raw_input('\n#Press enter to continue...')
        elif selection == '2':
            interfaces = port_channel_selection(allpclist,allepglist)
            print('\r')
          #      for number in sorted(pcsinglelist):
          #          data = """{{"fvRsPathAtt":{{"attributes":{{"encap":"{vlan}","instrImedcy":"immediate","tDn":"{}","status":"created"}},"children":[]}}}}""".format(numepgdict[number],vlan=vlan)
          #          print(data)
            #result, totalcount = PostandGetResponseData(url, data)
            option = custom_raw_input(("Would you like to do?\n\
                        \n1.) shut\
                        \n2.) no shut\
                        \n3.) bounce \n\
                        \nSelect a number: "))
            if option == '1':
                print('\n')
                shutinterfaces(interfaces)
            elif option == '2':
                print('\n')
                noshutinterfaces(interfaces)
            else:
                print('\n')
                shutinterfaces(interfaces)
                noshutinterfaces(interfaces)
            custom_raw_input('\n#Press enter to continue...')

        elif selection == '3':
            interfaces = port_channel_selection(allvpclist,allepglist)
            print('\r')
          #      for number in sorted(pcsinglelist):
          #          data = """{{"fvRsPathAtt":{{"attributes":{{"encap":"{vlan}","instrImedcy":"immediate","tDn":"{}","status":"created"}},"children":[]}}}}""".format(numepgdict[number],vlan=vlan)
          #          print(data)
            #result, totalcount = PostandGetResponseData(url, data)
            option = custom_raw_input(("Would you like to do?\n\
                        \n1.) shut\
                        \n2.) no shut\
                        \n3.) bounce \n\
                        \nSelect a number: "))
            if option == '1':
                print('\n')
                shutinterfaces(interfaces)
            elif option == '2':
                print('\n')
                noshutinterfaces(interfaces)
            else:
                print('\n')
                shutinterfaces(interfaces)
                noshutinterfaces(interfaces)
            custom_raw_input('\n#Press enter to continue...')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as k:
                print('\n\nEnding Script....\n')
                exit()