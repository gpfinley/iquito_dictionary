#!/usr/bin/python

import xml.etree.ElementTree as ET
import re
import string
import codecs
import sys

if len(sys.argv) > 1:
    LIFT_FILE = sys.argv[1]
else:
    LIFT_FILE = "iquito dictionary.lift" 
if len(sys.argv) > 2:
    LIFT_FILE = sys.argv[2]
else:
    ALPHAFILE = "iquito alphabet.txt"

# Scrub out characters from a word that will mess up LaTeX
# Also perform other LaTeX-readying operations (subscripting, e.g.)
def sanitize(word): 
    word = re.sub(r"\\iqt ","", word)
    word = re.sub(r"\\sp ","", word)
    word = re.sub(r"\\", "", word)
    word = re.sub("&", "\\&", word)
    word = re.sub("\$", "", word)
    word = re.sub("{", "", word)
    word = re.sub("}", "", word)
    word = re.sub("_([1-9])", "$_\\1$", word)
    return word

# SORTING FUNCTIONS

def gregSortKey(word, alphabet):
    i = 0
    score = "" 
    while i < len(word) :
        # check for digraphs (or trigraphs)
        char = getMaximalLetter(word[i:], alphabet)
        # And if we did use a long letter, be sure to update our counter

        if not char in alphabet : char = word[i]

        i += len(char) - 1

#        if not char in alphabet: 
#            char = 'default' 
        if char in alphabet:
            score += chr(alphabet[char])
#        score += ""
        i += 1
    return score 

# Finds the maximal letter in a string, beginning at a specified index.
# Good for digraphs, trigraphs, or larger (e.g., combining characters!)

def getMaximalLetter(word, alphabet) :
    substr = ''
    n = 0
    letter = word[n]
    while n < len(word) :
        substr += word[n]
        if substr in alphabet :
            letter = substr
            i = n
        n += 1
    return letter

# Sub out <span> tags
# FLEx's xml is bad
d = open(LIFT_FILE).read()
d = re.sub("<span[^>]*>","",d)
d = re.sub("</span>","",d)
tempname = "intermediate_lexicon.xml"
w =open(tempname,'w')
w.write(d)
w.close()

tree = ET.parse(tempname)
root = tree.getroot()

# Maps entry IDs to tuples containing (latexCommand, text)
tuplesByHeadword = {}

# Maps English/Spanish reversals to tuples containing (latexCommand, text)
tuplesByEngReversal = {}
tuplesBySpnReversal = {}

# Will map entry IDs to citation forms
citations = {}

duplicateCits = {}

print len(root.findall('entry'))

# Need to do a quick loop through to build a map between entry IDs and citation forms (for variants/references)
for entryNode in root.iter("entry"): 
    # citation form, or lexeme form if not present

    # use the iquito form if tagged as such, otherwise whatever you find there
    try:
        lexeme = entryNode.find('lexical-unit').find("./form[@lang='iqu']").find('text') 
    except:
        lexeme = entryNode.find('lexical-unit').find('.//text')
    try:
        citation = entryNode.find('citation').find('./form[@lang="iqu"]').find('text').text.encode('utf-8')
    except:
        citation = lexeme.text.encode('utf-8')
    entryId = entryNode.attrib['id'].encode('utf-8')

    if 'order' in entryNode.attrib:
        citation += "$_" + entryNode.attrib['order'] + "$"

    if type(citation) == unicode:
        print "UNICODE", citation
        citation = citation.encode('utf-8')

    # Make sure that we haven't already put this citation form in,
    #   as this will cause entries to be overwritten later
    for eid, cit in citations.items():
        if cit == citation:
            if not cit in duplicateCits:
                duplicateCits[cit] = [eid]
            duplicateCits[cit].append(entryId)

    citations[entryId] = citation

# Now add subscripts for any duplicate entries
for cit, eids in duplicateCits.items():
    for i in range(len(eids)):
        citations[eids[i]] += '$_' + str(i+1) + '$'

print len(citations)

# Now do the main loop and build up the actual text of everything

for entryNode in tree.iter("entry"):

    entryId = entryNode.attrib['id'].encode('utf-8')
#    print entryId

    # List of tuples: latex command, content
    t = []

    # lexeme form
    try:
        lexeme = entryNode.find('lexical-unit').find("./form[@lang='iqu']").find('text')#.text.encode('utf-8')
    except:
        lexeme = entryNode.find('lexical-unit').find('form').find('text')#.text.encode('utf-8')

    t.append( ('lexeme', lexeme.text.encode('utf-8')) )

    # deriv root field

    derivRoot = entryNode.find("./*[@type='Deriv Root']")
    if derivRoot != None:
        t.append(('derivroot', derivRoot.text.encode('utf-8')))

    # variant form field iff variant type = raiz imperfectivo 
    # Build these up for later. Only put things that are not raiz imperfectivo
    # Tuple structure
    variantFormTypes = [] 
    for relation in entryNode.findall("relation"):
        trait = relation.find(".//trait[@name='variant-type']")
        if trait is not None:
            if 'value' in trait.attrib:
                variantType = trait.attrib['value']
#                if variantType == 'ra\xc3\xadz imperfectivo': 
                if variantType[4:] == " imperfectivo":
                    try:
                        t.append(('raizImperfectivoVariantForm', relation.attrib['ref'].encode('utf-8')))
                    except:
                        "Couldn't add a variant form because there was no 'ref' attribute or it didn't match a dictionary entry"
                else:
                    try:
                        variantFormTypes.append( (relation.attrib['ref'].encode('utf-8'), variantType.encode('utf-8')) )
                    except:
                        "Couldn't add a variant form because there was no 'ref' attribute or it didn't match a dictionary entry"


    # irreg pl field 
    irregPl = entryNode.find("./field[@type='Irreg Pl']")
    if irregPl is not None:
        t.append( ('irregPl', irregPl.find(".//text").text.encode('utf-8') ) )

    # activemiddle field
    activemiddle = entryNode.find("./field[@type='activemiddle']")
    if activemiddle is not None:
        t.append( ('activemiddle', activemiddle.find(".//text").text.encode('utf-8') ) )

    # (sense-level info:)

    for sense in entryNode.iter("sense"):

        # grammatical info field (otherwise "none")
        grammaticalInfo = sense.find("grammatical-info")
        gramText = 'none'
        if grammaticalInfo is not None:
            try:
                gramText = grammaticalInfo.attrib['value'].encode('utf-8')
            except:
                print "Grammatical info didn't work for entry ID " + entryId
        t.append(('gramInfo', gramText))
                
        # sp gloss (otherwise "none")
        # eng gloss (otherwise "none")
        spnGloss = sense.find("./gloss[@lang='es']")
        engGloss = sense.find("./gloss[@lang='en']")
        if spnGloss is not None:
            t.append( ('spnGloss',spnGloss.find(".//text").text.encode('utf-8')) )
        else:
            t.append(('spnGloss','none'))
        if engGloss is not None:
            t.append( ('engGloss',engGloss.find(".//text").text.encode('utf-8')) )
        else:
            t.append(('engGloss','none'))

        spnReversals = []
        engReversals = []
        # spanish reversals entries field 
        # english reversals entries field 
        for reversal in sense.iter("reversal"):
            if reversal.attrib['type'] == 'es':
                spnReversals.append(reversal.find(".//text").text.encode('utf-8'))
            elif reversal.attrib['type'] == 'en':
                engReversals.append(reversal.find(".//text").text.encode('utf-8')) 
        for spnReversal in spnReversals:
            t.append(('spnReversal',spnReversal))
            tuplesBySpnReversal[spnReversal] = [('gramInfo',gramText),('headword',citations[entryId])]
        for engReversal in engReversals:
            t.append(('engReversal',engReversal))
            tuplesByEngReversal[engReversal] = [('gramInfo',gramText),('headword',citations[entryId])]

        # spanish definition field, otherwise "none" 
        # english definition field, otherwise "none"
        for definition in sense.findall("definition"):
            spnDef = definition.find("./form[@lang='es']")
            engDef = definition.find("./form[@lang='en']")
            if spnDef is not None:
                span = spnDef.find(".//span")
                if span is not None and span.text is not None:
                    text = span.text.encode('utf-8')
                else:
                    text = spnDef.find(".//text").text.encode('utf-8')
                t.append( ('spnDef',text) )
            else:
                t.append(('spnDef','none'))
            if engDef is not None:
                span = engDef.find(".//span")
                if span is not None and span.text is not None:
                    text = span.text.encode('utf-8')
                else:
                    text = engDef.find(".//text").text.encode('utf-8')
                t.append( ('engDef',text) )
            else:
                t.append(('engDef','none'))

        # scientific name field
        scientificName = sense.find("./field[@type='scientific-name']")
        if scientificName is not None:
            t.append( ('scientificName', scientificName.find(".//text").text.encode('utf-8') )) 

        spnGramNotes = []
        engGramNotes = []
        # Spanish grammatical notes
        # English grammatical notes
        for note in sense.findall("./note[@type='grammar']"):
            for form in note.findall("./form[@lang='es']"):
                span = form.find(".//text") 
                if span is not None and span.text is not None:
                    spnGramNotes.append(span.text.encode('utf-8'))
            for form in note.findall("./form[@lang='en']"):
                span = form.find(".//text") 
                if span is not None and span.text is not None:
                    engGramNotes.append(span.text.encode('utf-8'))
        for spnGramNote in spnGramNotes:
            t.append(('spnGramNote', spnGramNote))
        for engGramNote in engGramNotes:
            t.append(('engGramNote', engGramNote))


    # iterate for as many variants as necessary, but NOT raiz imperfecto:
    # contents of variant form field
    # contents of variant type field
    for variantFormType in variantFormTypes:
        t.append( ('variantForm', variantFormType[0] ) )
        t.append( ('variantType', variantFormType[1] ) )

    # Contents of date modified field
    t.append(('dateModified', entryNode.attrib['dateModified']))

    # Now add it to tupesById
    headword = citations[entryId]
    for aTuple in t:
        if(type(aTuple[1]) == unicode):
            print "UNICODE WHERE IT DOESN'T BELONG:", aTuple[1]
    if citations[entryId] in tuplesByHeadword:
        print "DUPLICATE ENTRY:", citations[entryId], entryId
    tuplesByHeadword[citations[entryId]] = t

print len(tuplesByHeadword)

sortedHeadwordEntryTuples = [ (headword,tuplesByHeadword[headword]) for headword in tuplesByHeadword.keys() ]

alphaData = open(ALPHAFILE,'r') 
i = 1
alphabet = {'default':0}   # The alphabet itself
headings = {}   # This dict contains what will be written for headings
keyName = ""    # Temporary variable (see below)

for line in alphaData:
    line = line.replace("\r",'')
    line = line.replace("\n",'')

    bothHalves = line.split("\t")
    try:
        keyName = bothHalves[0]
        characters = bothHalves[1]
    except:
        print("Alphabet file not configured properly.")

    for character in characters.split() :
        alphabet[character] = i
    headings[i] = keyName
    i += 1
alphaData.close()
sortedHeadwordEntryTuples.sort(key=(lambda x: gregSortKey(x[0], alphabet)))

sortedEngReversalEntryTuples = [(x,tuplesByEngReversal[x]) for x in tuplesByEngReversal.keys()]
sortedSpnReversalEntryTuples = [(x,tuplesBySpnReversal[x]) for x in tuplesBySpnReversal.keys()]
sortedEngReversalEntryTuples.sort(key=(lambda x: sanitize(x[0].lower().strip('"'))))
sortedSpnReversalEntryTuples.sort(key=(lambda x: gregSortKey(sanitize(x[0].lower().strip('"')), alphabet)))
#sortedEngReversalEntryTuples.sort(key=(lambda x: gregSortKey(sanitize(x[0].lower().strip('"')), engAlphabet)))

outfile = open('iquito_entries.tex','w')
customCommands = set()

for entry in sortedHeadwordEntryTuples:
    
    t = "".encode('utf-8')

    for thisTuple in entry[1]:
        try:
            textToAdd = thisTuple[1]
            # If it's a reference, use that citation form as is
            if textToAdd in citations:
                textToAdd = citations[textToAdd]
            else:
                textToAdd = sanitize(textToAdd)
            t += '\t\\' + thisTuple[0]
            t += '{' + textToAdd + '}\n'
            customCommands.add(thisTuple[0])
        except:
            print "problem with tuple "
            print thisTuple, entry

    t += '}\n\n'

    t = "\\entry{" + entry[0] + "}{\n" + t
    try:
        outfile.write(t)
    except:
        print "couldn't write", t

outfile.close()

outfileEng = open('english_reversal_entries.tex','w')
engCustomCommands = set()
for entry in sortedEngReversalEntryTuples: 
    t = "".encode('utf-8') 
    for thisTuple in entry[1]:
        try:
            textToAdd = sanitize(thisTuple[1])
            t += '\t\\' + thisTuple[0]
            t += '{' + textToAdd + '}\n'
            engCustomCommands.add(thisTuple[0])
        except:
            print "problem with tuple "
            print thisTuple, entry

    t += '}\n\n'

    t = "\\entry{" + sanitize(entry[0]) + "}{\n" + t
    try:
        outfileEng.write(t)
    except:
        print "couldn't write", t

outfileEng.close()

outfileSpn = open('spanish_reversal_entries.tex','w')
spnCustomCommands = set()
for entry in sortedSpnReversalEntryTuples: 
    t = "".encode('utf-8') 
    for thisTuple in entry[1]:
        try:
            textToAdd = sanitize(thisTuple[1])
            t += '\t\\' + thisTuple[0]
            t += '{' + textToAdd + '}\n'
            spnCustomCommands.add(thisTuple[0])
        except:
            print "problem with tuple "
            print thisTuple, entry

    t += '}\n\n'

    t = "\\entry{" + sanitize(entry[0]) + "}{\n" + t
    try:
        outfileSpn.write(t)
    except:
        print "couldn't write", t
outfileSpn.close()


print "You will need to define the following custom commands:"
headerString = """
\\newcommand{\entry}[2]{
    \\large#1\\normalsize \\newline
    #2\\nolinebreak
    \markboth{#1}{#1}\\nolinebreak
}
\\newcommand{\Numbering}[1]{\scriptsize\\textbf{#1}:\\normalsize}
\\newcommand{\NewLetter}[1]{\section*{#1}\\noindent\\\\}
"""
print headerString
for c in customCommands:
    print "\\newcommand{\\" + c + "}[1]{\\textbf{" + c + "}: #1\\newline}"

print "\nFor the English reversal:"
print headerString
for c in engCustomCommands:
    print "\\newcommand{\\" + c + "}[1]{\\textbf{" + c + "}: #1\\newline}"

print "\nFor the Spanish reversal:"
print headerString
for c in spnCustomCommands:
    print "\\newcommand{\\" + c + "}[1]{\\textbf{" + c + "}: #1\\newline}"
