#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

""" Some common utility classes used by tests """

from datetime import datetime, timedelta, tzinfo
import re

class SimpleOffsetTzInfo(tzinfo):    
    """ Very simple implementation of datetime.tzinfo offering set timezone offset for datetime instances """
    
    def __init__(self, offsetInHours=None):
        """ Constructs a new tzinfo instance using an amount of hours as an offset
        
        :param offsetInHours: The timezone offset, in hours (may be negative)
        :type offsetInHours: int or float
        """
        if offsetInHours != None: #pragma: no cover
            self.offsetInHours = offsetInHours        
    
    def utcoffset(self, dt):
        return timedelta(hours=self.offsetInHours)
    
    def dst(self, dt):
        return timedelta(0)
    
    def __repr__(self):
        return 'gsmmodem.util.SimpleOffsetTzInfo({0})'.format(self.offsetInHours)

def parseTextModeTimeStr(timeStr):
    """ Parses the specified SMS text mode time string
    
    The time stamp format is "yy/MM/dd,hh:mm:ss±zz"
    (yy = year, MM = month, dd = day, hh = hour, mm = minute, ss = second, zz = time zone
    [Note: the unit of time zone is a quarter of an hour])
    
    :param timeStr: The time string to parse
    :type timeStr: str
    
    :return: datetime object representing the specified time string
    :rtype: datetime.datetime
    """
    msgTime = timeStr[:-3]
    tzOffsetHours = int(int(timeStr[-3:]) * 0.25)
    return datetime.strptime(msgTime, '%y/%m/%d,%H:%M:%S').replace(tzinfo=SimpleOffsetTzInfo(tzOffsetHours))

def lineStartingWith(string, lines):
    """ Searches through the specified list of strings and returns the 
    first line starting with the specified search string, or None if not found
    """
    for line in lines:
        if line.startswith(string):
            return line
    else:
        return None

def lineMatching(regexStr, lines):
    """ Searches through the specified list of strings and returns the regular expression 
    match for the first line that matches the specified regex string, or None if no match was found

    Note: if you have a pre-compiled regex pattern, use lineMatchingPattern() instead

    :type regexStr: Regular expression string to use
    :type lines: List of lines to search

    :return: the regular expression match for the first line that matches the specified regex, or None if no match was found
    :rtype: re.Match
    """
    regex = re.compile(regexStr)
    for line in lines:
        m = regex.match(line)
        if m:
            return m
    else:
        return None

def lineMatchingPattern(pattern, lines):
    """ Searches through the specified list of strings and returns the regular expression 
    match for the first line that matches the specified pre-compiled regex pattern, or None if no match was found

    Note: if you are using a regex pattern string (i.e. not already compiled), use lineMatching() instead

    :type pattern: Compiled regular expression pattern to use
    :type lines: List of lines to search

    :return: the regular expression match for the first line that matches the specified regex, or None if no match was found
    :rtype: re.Match
    """
    for line in lines:
        m = pattern.match(line)
        if m:
            return m
    else:
        return None
    
def allLinesMatchingPattern(pattern, lines):
    """ Like lineMatchingPattern, but returns all lines that match the specified pattern

    :type pattern: Compiled regular expression pattern to use
    :type lines: List of lines to search

    :return: list of re.Match objects for each line matched, or an empty list if none matched
    :rtype: list
    """
    result = []
    for line in lines:
        m = pattern.match(line)
        if m:
            result.append(m)
    return result


def removeAtPrefix(string):
    """ Remove AT prefix from a specified string.

    :param string: An original string
    :type string: str

    :return: A string with AT prefix removed
    :rtype: str
    """
    if string.startswith('AT'):
        return string[2:]
    return string


gsm = (u"@£$¥èéùìòÇ\nØø\rÅå?_?????????\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>"
       u"?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
ext = (u"````````````````````^```````````````````{}`````\\````````````[~]`"
       u"|````````````````````````````````````?``````````````````````````")


def get_encode(currentByte, index, bitRightCount, position, nextPosition, leftShiftCount, bytesLength, bytes):
    if index < 8:
        byte = currentByte >> bitRightCount

        if nextPosition < bytesLength:
            idx2 = bytes[nextPosition]
            byte = byte | ((idx2) << leftShiftCount)
            byte = byte & 0x000000FF
        else:
            byte = byte & 0x000000FF

        final = (hex(byte)).upper()
        return final
    return ''


def gsm_encode(plaintext):
    res = ""
    f = -1
    t = 0
    bytes = getBytes(plaintext)
    bytesLength = len(bytes)
    for b in bytes:
        f = f + 1
        t = (f % 8) + 1
        st = str(get_encode(b, t, t - 1, f, f + 1, 8 - t, bytesLength, bytes))

        st = re.sub("b'", '', st)
        st = re.sub("'", '', st)
        if len(st) == 2:
            res += st

        elif len(st) == 4:
            # if 'C2' in st:
            res += st[2] + st[3]
        # else:

        #   res += st[0] + st[3]

    return res


def getBytes(plaintext):
    if type(plaintext) != str:
        plaintext = str(plaintext)
    bytes = []
    for c in plaintext:
        idx = gsm.find(c)
        if idx != -1:
            bytes.append(idx)
        else:
            idx = ext.find(c)
            if idx != -1:
                bytes.append(27)
                bytes.append(idx)
    return bytes


def chunks(l, n):
    if n < 1:
        n = 1
    return [l[i:i + n] for i in range(0, len(l), n)]


def gsm_decode(codedtext):
    hexparts = chunks(codedtext, 2)
    number = 0
    bitcount = 0
    output = ''
    found_external = False
    for byte in hexparts:
        byte = int(byte, 16);

        # add data on to the end
        number = number + (byte << bitcount)
        # increase the counter
        bitcount = bitcount + 1
        # output the first 7 bits
        if number % 128 == 27:
            '''skip'''
            found_external = True
        else:
            if found_external == True:
                character = ext[number % 128]
                found_external = False
            else:
                character = chr(number % 128)
            output = output + character

        # then throw them away
        number = number >> 7
        # every 7th letter you have an extra one in the buffer
        if bitcount == 7:
            if number % 128 == 27:
                '''skip'''
                found_external = True
            else:
                if found_external == True:
                    character = ext[number % 128]
                    found_external = False
                else:
                    character = chr(number % 128)
                output = output + character

            bitcount = 0
            number = 0
    return output


def _encode(code):
    tab = []
    for c in code:
        ch = str(bin(int(gsm_encode(c), 16))[2:])
        tab.append("0" * (7 - len(ch)) + ch)
    tabf = []
    f = -1
    t = 0
    count = 1
    for i in range(0, len(tab) - 1):

        if count == 1 and i == 0:
            f += 1
            t = (f % 8) + 1
            s = tab[i + 1][7 - t:] + tab[i]
            tabf.append(s[:8])
        elif count == 1 and i != 0:
            f += 1
            t = (f % 8) + 1
            s = tab[i + 1][7 - t:] + tab[i]
            tabf.append(s[:8])
        elif count != 8:
            f += 1
            t = (f % 8) + 1
            s = tab[i + 1][7 - t:] + tab[i]
            tabf.append(s[:8])
        elif count == 8:
            f += 1
            t = (f % 8) + 1
            s = tab[i]
            count = 0
        count += 1

    tabf.append("0" * (8 - len(tab[-1][:7 - t])) + tab[-1][:7 - t])
    final = ""
    for ta in tabf:
        ss = str(hex(int(ta, 2)))[2:]
        if len(ss) == 1:
            ss = "0" + ss
        final += ss.upper()
    return final
