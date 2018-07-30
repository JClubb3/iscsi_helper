#! /usr/bin/env python3

import argparse
import time
import sys
import os
from subprocess import Popen, PIPE

DRIVER = None

# argument parser and arguments
parser = argparse.ArgumentParser()

parser.add_argument("-i", "--ip", help="log into a specified disk on a given IP address", action="store")
parser.add_argument("-f", "--format", help="format a given disk ID", action="store")
parser.add_argument("-m", "--mount", help="mount a particular disk ID", action="store")
parser.add_argument("-c", "--copy", help="copy a given file from /mnt/data/ to the given mount point", action="store")
parser.add_argument("-d", "--diff", help="compare all the files in the given mount location to matching files in /mnt/data", action="store")
parser.add_argument("-l", "--logout", help="unmount and logout of all Cybernetics disks", action="store_true")
parser.add_argument("-s", "--session", help="show all current iscsi session", action="store_true")

def iscsisession():
    command0 = Popen(['sudo', 'iscsiadm', '-m', 'session'], stdout=PIPE, stderr=PIPE)
    outputprinter(command0)

def iscsilogin(ip, cyberdisk):
    command0 = Popen(['sudo', 'iscsiadm', '-m', 'discovery', '-t', 'st', '-p', ip], stdout=PIPE, stderr=PIPE)
    out0 = command0.stdout.read().decode("utf-8")
    print(out0)

    newlist = []
    lst = out0.split()
    for line in lst:
        if line[:3] == "eui" and line not in newlist:
            newlist.append(line)
    try:
        command1 = Popen(['sudo', 'iscsiadm', '-m', 'node', '-T', newlist[int(cyberdisk)], '-p', ip, '-l'], stdout=PIPE,
                     stderr=PIPE)
        outputprinter(command1)
    except IndexError:
        print("Either cannot find the specified disk, or cannot find any disks. Exiting.")
        sys.exit()

def format(cyberdisk):

    time.sleep(0.5)

    newerlist = cyberdiskfinder()

    if cyberdisk == "last" or int(cyberdisk) == -1:
        disk = newerlist[-1]
    else:
        disk = newerlist[int(cyberdisk)]

    p = Popen(['sudo', 'fdisk', '/dev/{}'.format(disk)], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    time.sleep(0.2)
    p1 = p.communicate(b'g\n'
                       b'n\n\n\n\n'
                       b'w\n')
    if p1[1]:
        print(p1[1].decode('utf-8'))
    else:
        print(p1[0].decode('utf-8'))
    time.sleep(0.2)
    p = Popen(['sudo', 'mkfs.ext4', '/dev/{}1'.format(disk)], stdout=PIPE, stderr=PIPE, stdin=PIPE)
    err = p.stderr.read().decode('utf-8')
    if "(y,n)" in err.split():
        p1 = p.communicate('y')
        print(p1[0].decode('utf-8'))
    else:
        out = p.stdout.read().decode('utf-8')
        print(out)



def mount(cyberdisk, mountpoint):

    time.sleep(2)

    newerlist = cyberdiskfinder()

    if cyberdisk == "last" or cyberdisk == "-1" or cyberdisk == -1:
        disk = newerlist[-1]
    else:
        disk = newerlist[int(cyberdisk)]

    command2 = Popen(['sudo', 'mount', '/dev/{}1'.format(disk), mountpoint], stdout=PIPE, stderr=PIPE)
    outputprinter(command2)

    time.sleep(0.2)
    command3 = Popen(['lsblk'], stdout=PIPE, stderr=PIPE)
    outputprinter(command3)

def copy(datafile, destination):

    time.sleep(0.5)

    command1 = Popen(['sudo', 'cp', datafile, destination], stdout=PIPE, stderr=PIPE)
    outputprinter(command1)

    command2 = Popen(['sync'], stdout=PIPE, stderr=PIPE)
    outputprinter(command2)

    command3 = Popen(['ls', destination], stdout=PIPE, stderr=PIPE)
    outputprinter(command3)

def diff(mountpointlist):

    time.sleep(0.5)

    for mount in mountpointlist:
        command1 = Popen(["ls", mount], stdout=PIPE, stderr=PIPE)
        filelist = command1.stdout.read().decode("utf-8")
        filelist = filelist.splitlines()
        for file in filelist:
            if file != "lost+found":
                command2 = Popen(["sudo", "diff", "-srq", "{0}/{1}".format(mount, file), "/mnt/data/{0}".format(file)], stdout=PIPE, stderr=PIPE)
                outputprinter(command2)

def logout():
    command1 = Popen('lsblk -o VENDOR,NAME,MOUNTPOINT | grep "CYBERNET" -A 1', stdout=PIPE, stderr=PIPE, shell=True)
    out1 = command1.stdout.read().decode("utf-8")
    out1 = out1.split()
    newerlist = []
    for x in out1:
        if x[:5] == "/mnt/":
            newerlist.append(x)

    for x in newerlist:
        command2 = Popen(['sudo', 'umount', x], stdout=PIPE, stderr=PIPE)
        err2 = command2.stderr.read().decode("utf-8")
        if err2:
            print(err2)
        time.sleep(0.2)

    command3 = Popen(['sudo', 'iscsiadm', '-m', 'session', '-u'], stdout=PIPE, stderr=PIPE)
    outputprinter(command3)

def argsplitter(arg:str) -> list:
    return arg.split(",")

def outputprinter(command: Popen):
    out3 = command.stdout.read().decode("utf-8")
    err3 = command.stderr.read().decode("utf-8")
    if out3:
        print(out3)
    if err3:
        print(err3)

def cyberdiskfinder():
    command1a = Popen('lsblk -o NAME,VENDOR | grep "CYBERNET"', stdout=PIPE, stderr=PIPE, shell=True)
    out1a = command1a.stdout.read().decode("utf-8")
    out1a = out1a.split()
    newerlist = []
    for x in out1a:
        if x[:2] == "sd":
            newerlist.append(x)
    return newerlist


if __name__ == "__main__":
    args = parser.parse_args()

    if args.session:
        iscsisession()

    if args.ip:
        splitip = argsplitter(args.ip)
        ip = splitip[0]
        cyberdisk = splitip[1]
        iscsilogin(ip, cyberdisk)

    if args.format:
        cyberdisk = args.format
        format(cyberdisk)

    if args.mount:
        splitmount = argsplitter(args.mount)
        cyberdisk = splitmount[0]
        mountpoint = "/mnt/" + splitmount[1]
        mount(cyberdisk, mountpoint)

    if args.copy:
        splitcopy = argsplitter(args.copy)
        destination = "/mnt/" + splitcopy.pop()
        if os.path.ismount(destination):
            for file in splitcopy:
                datafile = "/mnt/data/" + file
                copy(datafile, destination)
        else:
            print("Destionation {0} is not a mount point! Exiting.".format(destination))
            sys.exit()

    if args.diff:
        mountpointlist = []
        initmountpointlist = argsplitter(args.diff)
        for mount in initmountpointlist:
            point = "/mnt/" + mount
            mountpointlist.append(point)
        diff(mountpointlist)

    if args.logout:
        logout()
