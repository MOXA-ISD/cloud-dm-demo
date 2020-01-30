# -*- coding: utf-8 -*-
import dateutil.parser
import datetime

# 將 Azure Connection String 轉成 Python Dictionary, 方便讀取
# Input: A=123;B=456;C=789
# Ouput: Dictionary
def connectStringToDictionary(connectionString):
    words = connectionString.split(';')
    dictionary = {}
    for word in words:
        middleP = word.find('=')
        itemName = word[0:middleP]
        itemVaule = word[middleP+1:]
        dictionary[itemName] = itemVaule
    return dictionary

# 擷取 sub string
# Input: 原始字串, 起始字串, 結尾字串
# Ouput: Dictionary
def getSubstring(sourceString, startString, endString):
    if startString == None:
        leadingLen = 0
        startP = 0
    else:
        leadingLen = len(startString)
        startP = sourceString.index(startString)        
        if startP < 0:
            return None
    endP = sourceString.find(endString, startP)
    if endP < 0:
        return None
    return sourceString[startP+leadingLen:endP]


#
# Compare two DateTime
def isNewDate(firstDate, secondDate):
    if firstDate == None:
        return True
    firstDT = firstDate
    secondDT = secondDate
    if not isinstance(firstDate, datetime.datetime):
        firstDT = dateutil.parser.parse(firstDate)
    
    if not isinstance(secondDate, datetime.datetime):
        secondDT = dateutil.parser.parse(secondDate)

    if secondDT > firstDT:
        return True
    else:
        return False


    