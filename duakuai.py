
# section imports

from   tinydb    import TinyDB, Query, where
from   unidecode import unidecode
from   time      import sleep
from   copy      import deepcopy
from   time      import sleep

import random as rd

import sys
import re
import builtins

def print(*args, **argv):
    builtins.print(*args, **argv)
    builtins.print()

# section TODO

TODO = \
"""
recursive word search,
    not done,
    given a compound word, return 1. its definition, 2. the definitions of all the rhythms of its syllables,
    heigaheu -> heiga, gaheu -> hei, ga, heu,
intuitive flags,
    yes done,
    the flags right not follow the names of the fields in td.json. They should move to intuitive names,
    -h becomes -w (not head, but word),
multi json search,
    yes done,
    keep multiple json files to search words, each an independent dictionary,
    like, td.json and dictionary.json from hoemai's new dictionary,
    the intuitive flags would work better with this, because each dictionary woudl have different names for the same field,
flag map,
    yes done,
    map intuitive flags with each field in its corresponding database automatically,
help,
    not done,
    document how to use the app, print the documentation on call,
    :q help should return the flags usable, what each flag does, and where they break,
    as would :q help -hr,
distributed app,
    not done,
    make the thing run in several computers, so we don't need a server but we still have the bot as long as one host is logged in,
    maybe done automatically by discord? connect two instances of the bot: one in the tower, one in the cellphone
format indent,
    not done,
    given any number of sentences, format them in nesting style. ask zeokueqche, he made up the style.,
    ok, so, basically, all verbs are upper case, and their argyments are nested like python expressions. isnt it neat? :D,
whole document gloss,
    not done,
    translate every toaq word in an arbitrarily long document into its one word gloss.,
    a gloss is a one word translation, hoemai has them in his new and ~improved~ dictionary. I think they are a good idea.,
unicode regexp search,
    not done,
    search using full unicode, with dotless i and tone marks and all that.,
    probalby useful if we keep lots of sentences as examples,
sentence database!,
    not done,
    keep toaq sentences in a separate database,
    would make search easier to code, and cull unnecessary results,
    maybe a new table would work better?... NAH! ALL THE DATABASES ARE BELONG TO US!!,

"""

# section Glossary

Glossary = \
"""consult:    apply a qlist to a db
qlist:         a list of queries, only useful after compression.
compress:      turn a qlist into a single query
syllable:      a toaq syllable, often a root word with a definition. That is, semantically relevant.
palabra, word: the value being searched
db, database:  a list of entries, or the original dictionary of entries as read from the json
entry:         a single entry in the dictionary, a set of fields that describe a word and its properties.
instruction:   which of the highest level operations should the bot do (:q query :i insertion :? whatever your heart desires)
instruction argument: what comes after the :i but outside any flag. in :ql, l is the instruction argument.
action:        a single query in a qlist, ready to be collapsed. It is a dict, and has this structure: ['logic', 'field', 'value', 'function']
'logic':       either and or or
'field':       any of the fields in the data base
'value':       the value expected of the field in the database.
'function':    the comparison function between the value and the field.

"""

# section foundation

"regexp to match single syllables, for splitting words into syllables"
 #syllable = re.compile(r'[^q]{0,2}[aeiouy][aeiouy]?q?', re.IGNORECASE)
 #syllable = re.compile(r'[cs]?[^q]{0,2}[aeiouy][aeiouy]?q?', re.IGNORECASE)

syllable  = r'[cs]?'      # c in ch, s in sh
syllable += r'[^q]{0,2}'  # starting letter (and h in ch, sh)
syllable += r'[aeiouy]'   # starting vowel
syllable += r'[aeiouy]?'  # optional second vowel
syllable += r'q?'         # optional ending q
syllable  = re.compile(syllable, re.IGNORECASE)

"load the database"
class AdaptibleDB(TinyDB):

    def __init__(self, json_file, adapt_dictionary):
        self.adapt_dictionary = adapt_dictionary
        super().__init__(json_file)

    def adapt(self, qlist):
        quicky = [] #deepcopy(qlist)
        for entry in qlist:
            entry = deepcopy(entry)
            testin = self.adapt_dictionary[entry['field']]
            if testin:
                entry['field'] = self.adapt_dictionary[entry['field']]
                quicky.append(entry)
        return quicky

toaduaDic = {
    "word":"head",
    "frame":"frame",      # todo
    "keywords":"keywords",    # todo
    "id":"id",
    "definition":"body",
    "user":"user",
    "scope":"scope",      # language the entry is written in
    "votes":"votes",
    "score":"score",
    "notes":"notes",
    "type":"",
    "gloss":"gloss",
    "distribution":"",
    "namesake":"",
    "examples":"",
    "fields":"",
    }

hoemaiDic = {
    "word":"toaq",
    "frame":"frame",      # todo
    "keywords":"keywords",    # todo
    "id":"",
    "definition":"english",
    "user":"",
    "scope":"",      # language the entry is written in
    "votes":"",
    "score":"",
    "notes":"notes",
    "type":"type",
    "gloss":"gloss",
    "distribution":"distribution",
    "namesake":"namesake",
    "examples":"examples",
    "fields":"fields"
}

rvsDict  = {v:k for k, v in (list(toaduaDic.items()) + list(hoemaiDic.items())) if v}

def translate_query_from_db(query):
    return {rvsDict[k]:v for k, v in query.items() if k in rvsDict}

def translate_qlist(qlist):
    return [translate_query_from_db(q) for q in qlist]

#tq   = TinyDB("td.json")
tqa  = AdaptibleDB("td.json", toaduaDic)
hoe  = AdaptibleDB("dictionary.json", hoemaiDic)

filesDic = {
    "offi" : hoe,
    "comm" : tqa
}

# section order results

def chop(val, regexp=syllable):
    """Split a word into syllables.

    This is useful because most syllables in toaq mean something,
    and that informs the meaning of the compound word.
    """
    return re.findall(regexp, unidecode(val))

def ordena(entry_list, field, sylla):
    """list of entries, sorted by field from the value of sylla

    If sylla is empty, sort by dictionary order, with phrases after words.
    
    sylla: syllable by which to order words
    field: the field in the entry list that will be compared with sylla
    entry_list: the list of entries to be sorted.

    Sorting order:
    1) the sylla is a single meaningful syllable, start with the sylla
    2) has the sylla, but does not start 
    3) the sylla is a substring of another syllable
    4) the reference is a sentence of more than one word.

    1) ma, mara, mahi, mama
    2) gama, lama, gimaji
    3) mao, maoja, mumaomu
    4) Dua mama ma jai be da. Kaqgai baq gama rao si a daqmoa poho da.
    """
    def _sortBy(dck):
        """Give each entry a sorting value: [number, entry].

        While sorting, the number will be considered before the entry,
        letting me organize words by a category before using their dictionary order.

        dck: a dictionary entry, a python dictionary with key:value pairs
        field: which key's value will be used for sorting
        reference: the value for sorting
        chp: list of syllables in this entry's value
        """
        reference = dck[field]
        chp = chop(reference)
        if len(reference.split()) > 1:
            num = 4
        elif sylla in chp:
            if sylla == chp[0]:
                num = 1
            else:
                num = 2
        else:
            num = 3
        #print(num, sylla, chp)
        # return its type value, followed by its syllables
        return [num, chp]
    return sorted(list(entry_list), key=_sortBy)

def mycompressQuery(qlist):
    """join all queries into one gigaquery.

    how does it work?
    first,  reverse the queries in the query list
    second, fuse all the queries by nesting them, from rightmost to leftmost, like a b c d -> (a (b (c d)))
    """
    # the hierarchy of the qlist is: the further left you are, the higher priority you are
    # this does not fit with the application of query, so the list must be reversed appropriately

    # 1a 2b 3c 4d -> 4d c3 b2 a1
    qlist = [[a['logic'], a['field'], a['value'], match_fun_list[a['match_fun']]] for a in qlist]
    def _reorder(qlist):
        return list(reversed(qlist))
    lst = [[l, where(f).test(t, v)] for l, f, v, t in qlist]
    lst = _reorder(lst)

    def _compress(qlist):
        null, first = lst.pop(0)
        #print(null, first)
        for l, qry in lst:
            #print(l, qry)
            if l == 'and':
                first = first & qry
            else:
                first = first | qry
        return first

    #print(lst)
    return _compress(lst)

def consult(qlist, db):
    """Apply the query of the compressed qlist onto the db."""
    uberQuery = mycompressQuery(qlist)
    #print(uberQuery)
    return db.search(uberQuery)

 # organize by meaningful syllable
 # TODO organize by more than one syllable
 # sort consult, or cyllable consult
def sconsult(qlist, db):
    """Consult the compressed qlist onto the db, sorting them by the syllable order.

    I wanna sort the results by syllable, because syllables have meaning,
    and that way all words related to one another come together.
    But, if there are more than one meaningful syllable in the query,
    I don't know how to sort it.
    So, if there is only one word searched, we sort by that word.
    If there is more than one, sort by naive dictionary order,
    by passing to 'ordena' an empty 'sylla'
    """
    cnt = 0
    give_head = ""
    for q in qlist:
        if cnt > 1:
            break
        if q['field'] == 'word':
            cnt += 1
            give_head = q['value']
    qlist = db.adapt(qlist)
    sort_field = db.adapt_dictionary['word']
    return ordena(consult(qlist, db), sort_field, give_head)


# all these functions take a field value and a string, and return true if the string matches the field
# regexp search
def rsrch(field, regexp):
    """See if the regexp matches the value given for the field."""
    return re.compile(regexp, re.IGNORECASE).match(field)

# vanilla regexp search
def vrsrch(field, regexp):
    """Match without special characters.

    turn both the field value and the regexp into plain ascii before performing the match.
    """
    field, regexp = unidecode(field), unidecode(regexp)
    return rsrch(field, regexp)

# regular search
def srch(field, palabra):
    """Search for words that contain palabra anywhere within them."""
    field, palabra = unidecode(field), unidecode(palabra)
    regexp = ".*" + palabra + ".*"
    return rsrch(field, regexp)

# syllable search
def ssrch(field, palabra):
    """Return only words that contain palabra as a meaningful syllable.

    palabra: ma
    mama -> True
    maqme -> False
    """
    field, palabra = unidecode(field), unidecode(palabra)
    return palabra in chop(field)

# TODO is this function necessary? it seems that srch does its job and more
# it is if you want to search for special characters
def simple_substring(field, palabra):
    return palabra in field

def equality(field, palabra):
    """The field is the same as palabra"""
    field, palabra = unidecode(field), unidecode(palabra)
    return palabra == field

match_fun_list = {
        'regexp': vrsrch,
        'syllable': ssrch,
        'simple': srch, # TODO simple_substring
        'dictionary': srch,
        'exact': equality

        }

# section display

def see(db):
    """Print all words in the entries."""
    for i in db:
        print(i['head'], end="  ")
        #sleep(1)

def display(entry):
    """A very clumsy display of a full entry."""
    orden = ["head", "frame", "body", "apropos", "notes", "score"]
    print(entry[orden[0]]) #, "\t", entry[orden[1]])
    for o in orden[2:]:
        if o in entry:
            print("\t", o[0], entry[o])

def results(db, number):
    """A clumsy display of all entries in a result."""
    for entry in db[:number]:
        display(entry)

def display_conditional(entry, fields):
    """."""

    fies = ["word", "type", "frame", "distribution"]

    def _sie(field):
        if field in entry:
            out =  entry[field]
        elif field in ['type', 'frame', 'distribution']:
            out =  "---"
        else:
            out = ""
        return out
    longest = max([len(_sie(i)) for i in ['type', 'frame', 'distribution']])

    def _msie(field):
        return _sie(field).ljust(longest)

    l1 = "{}\t[{} : {} : {}]\n".format(*[_sie(f) for f in fies])
    lN = ""
    for f in fields:
        if f not in fies:
            lN += "\t{}\n".format(_sie(f))
    return l1 + lN

def dse(*args, **argv):
    """Simple way to change the display function."""
    return display_conditional(*args, **argv)

def display_all_entries(entries, fields):
    """Return all entries to be printed to discord"""
    all_entries = ""
    for entry in entries:
        all_entries += dse(entry, fields)
    return all_entries

# section insertion

def inserta(**entry):
    """Unfinished insertion into dictionary function."""
    if 'head' in entry and 'body' in entry:
        tq.insert(entry)

# section cli

# glossary: hydrolysis=split a cliString into its parts. monomer=part of a clistring. polymer=a clistring. monolysis=split a monomer. polymers are split into monomers. the results of a polymer inside a function are called pm. the results of a monomer inside a function are called mm. this comes form the first letter of each syllable in the word. polydict=the dictionary to parse the flag inputs. central=the first letter of a flag, representing the field, -hr| word, h is the central.

def hydrolysis(polymer):
    """Split a cli string into its query parts.

    "ql -h word -d definition" -> ["ql", "h word", "d definition"]
    """
    return polymer.split('-')

def monolysis(monomer):
    """Split a monomer into its parts: a monohead and a monobody.
    
    ":q10 tem ble que" -> [[q, 10],   tem, ble, que]
    monohead = mm[0]
    monobody = mm[1:]
    """
    monoheadSplitRegexp = "(\d+|\w|\||\+)"
    mm       = monomer.split(maxsplit=1)
    monohead = re.findall(monoheadSplitRegexp, mm[0])
    monobody = [m.strip() for m in mm[1:]]
    return   [monohead] + monobody

def polyheadlysis(monomer):
    mm = monolysis(monomer)
    return [mm[0]] + [mm[1].split() if mm[1:] else []]

def polylysis(polymer):
    """Split the polymer into a list of monomers, split the monomers into their monohead and monobody."""
    pm = hydrolysis(polymer)
    ph = polyheadlysis(pm.pop(0))
    return [ph] + [monolysis(pb) for pb in pm]

fields = {
    "w"     : "word",
    "f"     : "frame",      # todo
    "k"     : "keywords",    # todo
    "i"     : "id",
    "d"     : "definition",
    "u"     : "user",
    "s"     : "scope",      # language the entry is written in
    "v"     : "votes",
    "r"     : "score",
    "n"     : "notes",
    "y"     : "type",
    "g"     : "gloss",
    "i"     : "distribution",
    "a"     : "namesake",
    "e"     : "examples",
    "l"     : "fields"
    }

fieldslogic = {
        "|"     : ('logic', "or")
        }

fieldssearch = {
        "r"     : ("match_fun", "regexp"),
        "s"     : ("match_fun", "syllable"),
        "e"     : ("match_fun", "exact")
        }

fieldsmodify = {
        "+"     : "append"  # todo
        }

midict = {}
midict['central'] = fields

midict['terminal'] = {}
midict['terminal'].update(fieldslogic)
midict['terminal'].update(fieldssearch)
midict['terminal'].update(fieldsmodify)

def mkquery(monomere, reference):
    [[central, *terminal], *monobody] = monomere
    word = monobody[0]
    dick = {}
    try:
        dick['field'] = reference['central'][central]
        dick['value'] = word
        for t in terminal:
            tt = reference['terminal'][t]
            dick[tt[0]] = tt[1]
    except Exception as e:
        raise e
    return dick

def queryDefaults(action):
    """Fill the categories missing from mkquery with their default values."""
    if not 'logic' in action:
        action['logic'] = 'and'
    if not 'match_fun' in action:
        action['match_fun'] = 'simple'
    return action

def mymkqlist(polybody, reference):
    """Take all the actions that result from parsing a command, and turn each into a query that can can be joined by compressQuery."""
    compiled = [queryDefaults(mkquery(a, reference)) for a in polybody]
    return compiled

def query_exe(qlist, dblist=[tqa]):
    fullresult = []
    #print(qlist)
    for db in dblist:
        fullresult.extend(sconsult(qlist, db))
    return fullresult

def which_dic(polyheadbody):
    if polyheadbody:
        return [filesDic[f] for f in polyheadbody]
    return [hoe, tqa] # default

def which_fie(polyheadbody):
    if polyheadbody:
        return polyheadbody
    return ["definition"]


def fill_phb(phb):
    phb = phb.copy()
    if phb:
        if len(phb) == 1:
            if phb[0].startswith("d"):
                phb.append("f")
            else:
                phb.append("d")
    else:
        phb.append("f")
        phb.append("d")
    return phb

def parse_phb(phb):

    one = phb[0].split('+')
    two = phb[1].split('+')
    if one[0] == "d":
        dicks = one[1:]
        fields = two[1:]
    else:
        dicks = two[1:]
        fields = one[1:]
    return dicks, fields



# central, terminal
def interpret(cliString):
    pm = polylysis(cliString)
    [[[polyheadcentral, *polyheadterminal], polyheadbody], *polybody] = pm

    numbers_in_terminal = re.findall('\d+', "".join(polyheadterminal))
    number_of_results = int(numbers_in_terminal[0]) if numbers_in_terminal else 3

    #dictionaries = [hoe, tqa] # which files to search, in what order
    mdicks, mfields = parse_phb(fill_phb(polyheadbody))
    dictionaries = which_dic(mdicks)
    fields_to_display = which_fie(mfields)

    if polyheadcentral == 'q':
        mkql = mymkqlist(polybody, midict)
        query_result = query_exe(mkql, dictionaries)
        if 'l' in polyheadterminal:
            out = str(len(query_result))
        else:
            if 'A' in polyheadterminal:
                out = query_result
            else:
                out = query_result[:number_of_results]
            out = display_all_entries(translate_qlist(out), fields_to_display)
        return out
    elif polyheadcentral == 'h':
        return "TODO"

    return ""

def main(cliString):
    """Return a string of results for the cliString query."""
    try:
        res = interpret(cliString)
        if res:
            if re.compile("\d+").match(res):
                ret = res
            else:
                ret = res
        else:
            phrases = ["¯\_(ツ)_/¯ your search came empty"]
            ret = rd.choice(phrases)
    except BaseException as e:
        ret = ">~< cough (xAx) an error occured"
    return ret

def climain(cliString):
    print(main(cliString))


if __name__ == "__main__":
    builtins.print(main(sys.argv[1]))
