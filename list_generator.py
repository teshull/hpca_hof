import argparse
import operator
import re
import codecs
import sys
from lxml import etree


pageRegex = re.compile("([0-9]+)-([0-9]+)")
startYear = 1995
endYear = 2020
xmlFolder = "./xml"
outputFile = "out.txt"


def printOutInfo(container, rankings, filename, numRange=0):
    text_file = codecs.open(filename, mode='w+', encoding='utf-8')
    if numRange == 0:
        numRange = len(rankings)
    for num in range(numRange):
        author = rankings[num][0]
        line = author + " (total=" + str(rankings[num][1]) + "): "
        for y in range(startYear, endYear+1):
            year = str(y)
            numPapers = container[author].get(year, 0)
            line = "%s%d," % (line, numPapers)
        text_file.write(line+"\n")


def addToCount(container, key):
    count = container.get(key, 0) + 1
    container[key] = count


def addAuthorInfo(container, author, year):
    if author not in container:
        container[author] = {}
    addToCount(container[author], year)


def processElement(authorCount, authorData, paper):
    # false conference match
    if("conf/hpcasia" in paper.attrib["key"]):
        return False

    #checking for invalid matches
    pages = paper.xpath('pages')[0].text
    regexResult = pageRegex.match(pages)
    if(not regexResult):
        return False
    year = paper.xpath('year')[0].text
    yearNum = int(year)
    if(yearNum < startYear or yearNum > endYear):
        return False

    authors = paper.xpath('author')
    pageLength = int(regexResult.group(2)) - int(regexResult.group(1)) + 1
    # adding this because some workshops are included and had 8 page papers
    criteria = ((pageLength > 6 and yearNum < 2015) or
                 (pageLength >=3 and yearNum == 1999) or
                 (pageLength >=10 and yearNum >= 2015))
    if(not criteria):
        print "found paper not meeting criteria"
        print "pageLength:  ", pageLength
        print "year: ", year
        print "attribute: ", paper.attrib["key"]
        output = "authors: "
        for author in authors:
            output += author.text + ", "
        print output
        return False

    for author in authors:
        addToCount(authorCount, author.text)
        addAuthorInfo(authorData, author.text, year)
    return True



def eventDrivenParsing():
    count = 0
    #map contains number of papers for author
    authorCount = {}
    #map containing number of papers for author in each year
    authorData = {}
    fileName = "%s/dblp.xml" % (xmlFolder)
    for _, element in etree.iterparse(fileName, load_dtd=True,
                                          dtd_validation=True, huge_tree=True):
        if(element.tag == "inproceedings"):
            if("conf/hpca" in element.attrib["key"]):
                if(processElement(authorCount, authorData, element)):
                    count += 1
            #since no longer needed, free up memory allocated to element
            element.clear()

    print "total count = ", count
    sortedResult = sorted(authorCount.items(), key=operator.itemgetter(1),
                           reverse=True)
    printOutInfo(authorData, sortedResult, outputFile)


def parseArgs():
    global xmlFolder, startYear, endYear, outputFile
    parser = argparse.ArgumentParser(prog='HPCA HOF List Generator')
    parser.add_argument('--xmlFolder',
                        default=xmlFolder,
                        help='location of xml folder')
    parser.add_argument('--startYear',
                        default=startYear,
                        help='first year to count')
    parser.add_argument('--endYear',
                        default=endYear,
                        help='last year to count')
    parser.add_argument('--outputFile',
                        default=outputFile,
                        help='where to write results')

    args = parser.parse_args()
    xmlFolder = args.xmlFolder
    outputFile = args.outputFile
    startYear = int(args.startYear)
    endYear = int(args.endYear)

def main():
    parseArgs()
    eventDrivenParsing()

if __name__ == '__main__':
    main()
