#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
import os
import subprocess

#Config
# TODO: Make it be configurable outside the script (ConfigParser module?)
REPLACE_NUMBERS = True
QUICK_NUMBER_MODE = True
EXCEPTIONS = ['rz', 'sz', 'cz', 'sz', 'dz', 'dż']
#Only one letter keywords are currently supproted!
KEYWORDS = [('z','s'),('t','d'),('n',),('m',),('r',),('l',),('j'),('k','g'),('w','f'),('p','b')]

INFO = """
Quick and dirty script that helps in finding a word for a given number according to
  mnemonic major system.
Usage: prompter.py -g[e] aspell_language_code - generates word list if 'e' is
           present, extended aspell word list is created (not recommended)
       prompter.py [-p] search_string word_list - searches word_list file for
           search_string pattern. -p 
       Pattern is a regular regexp with few exceptions:
         - '#' is treated as any number of meaningless characters (= not a keyword or exception)
         - numbers are converted to corresponding keywords and wrapped with "#"
            (this behaviour depends on settings inside script actually)
"""

def create_word_list(lang_code, extended=False):
    if os.name != 'posix':
        print("Sorry, generating word list is supported only on posix systems!")
        return
    #initializing variables
    basic_cmd = r'aspell -l {lc} dump master | grep -Eo "^[^/]*" > {filename}'
    extended_cmd = r"aspell -l {lc} dump master | "\
        r"aspell -l {lc} expand | tr ' ' '\n' > {filename}"
    filename = "{0}{1}.txt".format(lang_code, "_ext" if extended else "")
    #actual action
    print("Creating {0} word list for language code '{1}'"\
        .format("extended" if extended else "basic", lang_code))
    cmd = (extended_cmd if extended else basic_cmd)\
        .format(lc=lang_code, filename=filename)
    print("Generating word list...")
    print("  Executing '{0}'".format(cmd))
    subprocess.call(cmd, shell=True)


def create_search_pattern(input_pattern):
    #Parsing settings
    p_exc = '|'.join(EXCEPTIONS)
    #Will work only for one-letter keywords (because of how [^...])
    # TODO: find a way to negate a group of words
    p_not_keywords = '[^\n'+''.join([''.join(k) for k in KEYWORDS])+']'
    #generating junk pattern (a non matching group of not keyword or exception)
    junk = '(?:'+p_exc+'|'+p_not_keywords+')'
    #Replacing numbers for their letter equivalents
    if REPLACE_NUMBERS:
        for i in range(10):
            input_pattern = input_pattern.replace(str(i),
            #Add '#' according to settings
                "#"*QUICK_NUMBER_MODE
                +'('+'|'.join(KEYWORDS[i])+')'
                +"#"*QUICK_NUMBER_MODE)

    # TODO: Make those non regexp special characters escapable
    #Remove multipile hashes (redundant)
    while(input_pattern.find("##") >= 0):
        input_pattern = input_pattern.replace("##", "#")
    
    #print("resolved input (simple): " + input_pattern)
    #Treating "#" as any meaningless character ('junk')
    pattern = "^("+input_pattern.replace("#","{0}*").format(junk)+")$"
    #print("resolved input (full): " + pattern)
    return re.compile(pattern, re.MULTILINE | re.UNICODE | re.IGNORECASE)


def find(word_list, pattern):
    for match in re.finditer(pattern, word_list):
        yield match

def pretty_print(match):
    # TODO: add different styles
    s = match.group()
    new_string = ""
    pos = match.start(0)
    starts = []
    ends = []
    startc = "("
    endc = ")"
    for i, g in enumerate(match.groups()):
        #skip 'main' match group
        if i == 0: continue
        starts.append(match.start(i+1) - pos)
        ends.append(match.end(i+1) - pos)
    
    for i, c in enumerate(s):
        if i in ends: new_string += endc
        if i in starts: new_string += startc
        new_string += c

    if i+1 in ends: new_string += endc
    print(new_string)


if __name__ == "__main__":
    # TODO: use optparse module instead of all this
    l = len(sys.argv)
    args = sys.argv
    if l <= 1:
        print(INFO)
        exit()
    if args[1].startswith('-g'):
        extended = 'e' in args[1]
        create_word_list(args[2], extended)
    else:
        prettyprint = False
        i_pattern = 1
        i_filename = 2
        if args[1].startswith('-'):
            i_pattern += 1
            i_filename += 1
            prettyprint = 'p' in args[1]
        
        pattern = create_search_pattern(args[i_pattern])
        filename = "pl.txt" if l <= i_filename else args[i_filename]
        #print("Searching for {0}  in {1}...".format(args[i_pattern], filename))
        words = open(filename).read()
        for match in find(words, pattern):
            if prettyprint:
                pretty_print(match)
            else:
                print(match.group())
            
