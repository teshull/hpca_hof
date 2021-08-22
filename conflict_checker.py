#!/usr/bin/python3

import argparse
import re
import codecs
import os
import sys
from nameparser import HumanName

nameExtraction1 = re.compile("([^0-9]+) \(total=(\d+)\)")
nameExtraction2 = re.compile("([^0-9]+) ([0-9]+) \(total=(\d+)\)")
writeToFile = True
conflictFilename = "script_conflicts.txt"
inputFilename = "out.txt"
thresholdCount = 8
NO_CONFLICT = -1


def readFile(filename="out.txt"):
    numFound = 0
    names = []
    totalNum = 0
    textFile = codecs.open(filename, mode='r', encoding='utf-8')
    for line in textFile:
        totalNum += 1
        regexResult = nameExtraction1.search(line)
        if(regexResult):
            name = HumanName(regexResult.group(1))
            name.total = int(regexResult.group(2))
            name.index = numFound
            name.original = regexResult.group(1)
            names.append(name)
            numFound += 1
        else:
            regexResult = nameExtraction2.search(line)
            if(regexResult):
                name = HumanName(regexResult.group(1))
                name.total = int(regexResult.group(3))
                name.index = numFound
                name.original = "%s %s" % (regexResult.group(1), regexResult.group(2))
                names.append(name)
                numFound += 1
            else:
                print("failed on line: ", line)
                sys.exit(1)
    print("Total number found = ", numFound)
    print("Total number missing = ", (totalNum - numFound))
    return names

#merging two conflict group IDs together
def changeConflictID(conflicts, oldVal, newVal):
    for i in range(len(conflicts)):
        if conflicts[i] == oldVal:
            conflicts[i] = newVal

# assigning all conflicts same group ID
def assignConflictGroup(conflicts, name, conflictNames):
    index = name.index
    value = index
    if conflicts[index] == NO_CONFLICT:
        conflicts[index] = value
    else:
        value = conflicts[index]

    for cName in conflictNames:
        cIndex = cName.index
        cValue = conflicts[cIndex]
        if cValue == NO_CONFLICT:
            conflicts[cIndex] = value
        elif cValue != value:
            changeConflictID(conflicts, cValue, value)


def nameChecks(names):
    # map of assigning each conflict to a group number
    conflicts = {}
    #stating all conflicts are unset
    for i in range(len(names)):
        conflicts[i] = NO_CONFLICT

    for i in range(len(names) - 1):
        name = names[i]
        remainingNames = names[i+1:]
        conflictNames = []
        nameMatch(name, remainingNames, conflictNames)
        reverseName(name, remainingNames, conflictNames)
        nickNameMatch(name, remainingNames, conflictNames)
        # reverseNickName(name, names, conflictNames)
        assignConflictGroup(conflicts, name, conflictNames)

    printIssues(conflicts, names)


def writeOutput(line):
    if(writeToFile):
        text_file = codecs.open(conflictFilename, mode='a+', encoding='utf-8')
        text_file.write(line + "\n")
    else:
        print(line)


def printIssues(conflicts, names):
    for i in range(len(conflicts)):
        group = []
        for j in range(len(conflicts)):
            value = conflicts[j]
            if value == i:
                group.append(names[j])
        if(len(group)) > 1:
            totalNum = 0
            for name in group:
                totalNum += name.total
            if totalNum >= thresholdCount:
                writeOutput("****ISSUE****")
                for name in group:
                    writeOutput(name.original + " " + str(name.total))
                writeOutput("total: " + str(totalNum))
                writeOutput("****END ISSUE****")


def nameMatch(name, names, conflicts):
    for n in names:
        if n.first == name.first:
            if n.last == name.last:
                conflicts.append(n)


def nickNameMatch(name, names, conflicts):
    if name.first == "":
        return
    for n in names:
        if n.first == "":
            continue
        if n.first[0] == name.first[0]:
            if n.last == name.last:
                conflicts.append(n)


def reverseName(name, names, conflicts):
    for n in names:
        if n.first == name.last:
            if n.last == name.first:
                conflicts.append(n)


def reverseNickName(name, names, conflicts):
    for n in names:
        if n.first == name.last:
            if n.last == name.first:
                conflicts.append(n)

def parseArgs():
    global inputFilename, conflictFilename, thresholdCount
    parser = argparse.ArgumentParser(prog='HOF Conflict Checker')
    parser.add_argument('--inputFile',
                        default=inputFilename,
                        help='location of list')
    parser.add_argument('--outputFile',
                        default=conflictFilename,
                        help='where to write conflicts')
    parser.add_argument('--threshold',
                        default=thresholdCount,
                        help='minimum for potential HOF candidate')

    args = parser.parse_args()
    inputFilename = args.inputFile
    conflictFilename = args.outputFile
    thresholdCount = int(args.threshold)

def main():
    parseArgs()
    names = readFile()
    nameChecks(names)


if __name__ == '__main__':
    main()
