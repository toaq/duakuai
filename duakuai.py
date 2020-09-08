import json
from tinydb import TinyDB, Query, where
from unidecode import unidecode
import re
from time import sleep
import sys
# TODO

TODO = {
        1:["recursive word search",
            "not done",
            "given a compound word, return 1. its definition, 2. the definitions of all the rhythms of its syllables",
            "heigaheu -> heiga, gaheu -> hei, ga, heu"],
        2:["intuitive flags",
            "not done",
            "the flags right not follow the names of the fields in td.json. They should move to intuitive names",
            "-h becomes -w (not head, but word)"],
        3:["multi json search",
            "not done",
            "keep multiple json files to search words, each an independent dictionary",
            "like, td.json and dictionary.json from hoemai's new dictionary",
            "the intuitive flags would work better with this, because each dictionary woudl have different names for the same field"],
        3.1:["flag map",
            "not done",
            "map intuitive flags with each field in its corresponding database automatically"],
        4:["help",
            "not done",
            "document how to use the app, print the documentation on call",
            ":q help should return the flags usable, what each flag does, and where they break",
            "as would :q help -hr"],
        5:["distributed app",
            "not done",
            "make the thing run in several computers, so we don't need a server but we still have the bot as long as one host is logged in"],
        6:["format indent",
            "not done",
            "given any number of sentences, format them in nesting style. ask zeokueqche, he made up the style.",
            "ok, so, basically, all verbs are upper case, and their argyments are nested like python expressions. isnt it neat? :D"]
        7:["whole document gloss",
            "not done",
            "translate every toaq word in an arbitrarily long document into its one word gloss.",
            "a gloss is a one word translation, hoemai has them in his new and ~improved~ dictionary. I think they are a good idea."],
        8:["unicode regexp search",
            "not done",
            "search using full unicode, with dotless i and tone marks and all that.",
            "probalby useful if we keep lots of sentences as examples"],
        9:["sentence database!",
            "not done",
            "keep toaq sentences in a separate database",
            "would make search easier to code, and cull unnecessary results",
            "maybe a new table would work better?... NAH! ALL THE DATABASES ARE BELONG TO US!!"],



            
        "infinity":"nothing"
        }

# foundation

"regexp to match single syllables, for splitting words into syllables"
#syllable = re.compile(r'[^q]{0,2}[aeiouy][aeiouy]?q?', re.IGNORECASE)
#syllable = re.compile(r'[cs]?[^q]{0,2}[aeiouy][aeiouy]?q?', re.IGNORECASE)

syllable = r'[cs]?' # c in ch, s in sh
syllable += r'[^q]{0,2}' # starting letter (and h in ch, sh)
syllable += r'[aeiouy]' # starting vowel
syllable += r'[aeiouy]?' # optional second vowel
syllable += r'q?' # optional ending q
syllable = re.compile(syllable, re.IGNORECASE)

"load the database"
tq = TinyDB("td.json")
word = Query()

# Dumb, uneccesary, ignorable
# these functions I made long before I had any idea what I was doing,
# they are not used in the rest of the code, but they might be useful for debugging.
# just ignore them

def reTest(val, target=syllable):
    """Dumb Test, true if it fits into toaq syllable structure."""
    return target.match(unidecode(val))

def unary():
    """Dumb Test, return all entries that match toaq syllables."""
    return tq.search(word.head.test(reTest))

def extract_symbols():
    """Dumb, get all unique symbols in the database for the words."""
    database = unary()
    _words = [a['head'] for a in database]
    _small = sorted(list(set([a for a in "".join(_words)])))
    return _small

def sk(test, target):
    """Find all that match the target through the test."""
    return tq.search(word.head.test(test, target))

# dictionary better

def chop(val, regexp=syllable):
    """Split a word into syllables.

    This is useful because most syllables in toaq mean something,
    and that informs the meaning of the compound word.
    """
    return re.findall(regexp, unidecode(val))

def ordena(db, field, palabra):
    """list of entries, sorted by field.

    Sorting order:
    1) the palabra is a single menaingful syllable, start with the palabra
    2) has the palabra, but does not start 
    3) the palabra is a substring of another syllable
    4) the reference is a sentence of more than one word.

    1) ma, mara, mahi, mama
    2) gama, lama, gimaji
    3) mao, maoja, mumaomu
    4) Dua mama ma jai be da. Kaqgai baq gama rao si a daqmoa poho da.
    """
    def _sortBy(dck):
        reference = dck[field]
        chp = chop(reference)
        if len(reference.split()) > 1:
            num = 4
        elif palabra in chp:
            if palabra == chp[0]:
                num = 1
            else:
                num = 2
        else:
            num = 3
        #print(num, palabra, chp)
        return [num, chp]
    return sorted(list(db), key=_sortBy)

# query list, data base
# query list: [[logic, field, value, test], ... ]

# elements to the left take precedence to elements on the right
aqlist = [
        ['empty', 'head', 'mui', lambda f, v: re.compile(v).match(f)], 
        ['and', 'body', 'predicate', lambda f, v: v in f],
        ['or', 'user', 'spreadsheet', lambda f, v: re.compile(v).match(f)]
        ]


def compressQuery(qlist):
    """Join all queries into one GigaQuery."""
    # the hierarchy of the qlist is: the further left you are, the higher priority you are
    # this does not fit with the application of query, so the list must be reversed appropriately

    # 1a 2b 3c 4d -> 4d c3 b2 a1
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
    uberQuery = compressQuery(qlist)
    return db.search(uberQuery)

# organize by meaningful syllable
# TODO organize by more than one syllable
# sort consult
def sconsult(qlist, db=tq):
    """Only searches for one head, not or-ing many. useful for sorting by sillable. TODO."""
    # get the head from the qlist, not extra from palabra
    cnt = 0
    give_head = ""
    for q in qlist:
        if cnt > 1:
            break
        if 'head' in q:
            cnt += 1
            give_head = q[2]
    return ordena(consult(qlist, db), 'head', give_head)


# regexp search
def rsrch(field, regexp):
    """TODO """
    return re.compile(regexp, re.IGNORECASE).match(field)

# vanilla regexp search
def vrsrch(field, regexp):
    field, regexp = unidecode(field), unidecode(regexp)
    return re.compile(regexp, re.IGNORECASE).match(field)

def srch(field, palabra):
    """Search for words that contain palabra anywhere within them."""
    field, palabra = unidecode(field), unidecode(palabra)
    regexp = ".*" + palabra + ".*"
    return rsrch(field, regexp)

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
    return palabra == field

match_fun_list = {
        'regexp': vrsrch,
        'syllable': ssrch,
        'simple': srch, # TODO simple_substring
        'dictionary': srch

        }

# display

def see(db):
    for i in db:
        print(i['head'], end="  ")
        #sleep(1)

def display(entry):
    orden = ["head", "frame", "body", "apropos", "notes", "score"]
    print(entry[orden[0]]) #, "\t", entry[orden[1]])
    for o in orden[2:]:
        if o in entry:
            print("\t", o[0], entry[o])

def results(db, number):
    for entry in db[:number]:
        display(entry)

def display_single_entry(entry):
    orden = ["head", "frame", "body", "apropos", "notes", "score", "user"]
    intermedio = {}
    for i in orden:
        if i in entry:
            val = entry[i]
        else:
            val = ""
        intermedio[i] = val
    parte = "".join(
            [
                f"{intermedio['head']}\tframe: {intermedio['frame']}\n",
                f"\tbody:\t{intermedio['body']}\n",
                #f"\tapropos:\t{intermedio['apropos']}\n",
                #f"\tnotes:\t{intermedio['notes']}\n",
                #f"\tscore:\t{intermedio['score']}\n"
                f"\tuser:\t{intermedio['user']}\n"
                
                ""
                ])
    return parte

def display_all_entries(entries):
    all_entries = ""
    for entry in entries:
        all_entries += display_single_entry(entry)
    return all_entries

# insertion

def inserta(**entry):
    if 'head' in entry and 'body' in entry:
        tq.insert(entry)

# cli

tests = [
        ":q -hr agatha -f sa -a gaslight fantasy -d girl genious",
        ":i word -f lu -d questionable content ___. ___ dumbing ___.",
        ":bw",
        ":b",
        ":bm index -f lu -a+ bitter sweet candy bowl",
        ":h q"
        ]

def pieces(command):
    return [p.split() for p in command.split('-')]

# pcommand - pieces command
# TODO change names of comma and comm and com1, they are all ugly as fuck
def parse(pcommand):
    """Return a representation of everything that must be done.

    [instruction, {action}, {action},...]
    instruction = all in comma dict
    action = {'logic':('and'/'or), 'field':all-in-the-dict-fields, 'value':what will be searched, 'match_fun':how to idenrify it}
    """
    # commands = q, qU, i, iU, bw, bu, bm, h
    comma = {
            "q"     : "query",
            "i"     : "insert", # TODO
            "b"     : "buffer", # TODO
            "h"     : "help"    # TODO
            }

    queryModifiers = {
            "l"     : "length",
            "A"     : "all"
            }

    commaPlus = {
            "w"     : "write",  # TODO
            "u"     : "undo",   # TODO
            "m"     : "modify", # TODO
            "U"     : "unicode support" # TODO
            }

    # flags = h, hr, hs, f, a, a+, i, b, b+, u, l, v+, s, n, n+
    # flags = h|, f|, i|, ..., hr|, hs|, ..., br|, ...
    fields = {
            "h"     : "head",
            "f"     : "frame",      # TODO
            "a"     : "apropos",    # TODO
            "i"     : "id",
            "b"     : "body",
            "u"     : "user",
            "l"     : "scope",      # language the entry is written in
            "v"     : "votes",
            "s"     : "score",
            "n"     : "notes"
            }

    fieldsLogic = {
            "|"     : "or"
            }

    fieldsSearch = {
            "r"     : "regexp",
            "s"     : "syllable"
            }

    fieldsModify = {
            "+"     : "append"  # TODO
            }


    def _interpret_flag(flag):
        lst = [l for l in flag]
        action = {}
        action['field'] = fields[lst.pop(0)]
        for l in lst:
            if l in fieldsLogic:
                action['logic'] = fieldsLogic[l]
            elif l in fieldsSearch:
                action['match_fun'] = fieldsSearch[l]
            else:
                raise Exception('unrecognized flag')
        return action
    
    def _defaults(action):
        if not 'logic' in action:
            action['logic'] = 'and'
        if not 'match_fun' in action:
            action['match_fun'] = 'simple'
        return action

    def _complete(action, value):
        action['value'] = value
        return action

    def _come_together(flag, value):
        return _complete(_defaults(_interpret_flag(flag)), value)


    comm = pieces(pcommand)
    #com1 = [(flag, palabra, _come_together(flag, palabra)) for flag, palabra in comm[1:]]
    try:
        com1 = [_come_together(flag, palabra) for flag, palabra in comm[1:]]
    except ValueError:
        raise Exception('value missing')

    # instr is a string of the form :q[l|10]
    # TODO ugly access, gotta parse the instr prettier
    def _parse_instruction(instr):
        instr = instr[1:]
        ins = instr[0]
        #print(ins, instr)
        lst = [comma[ins]]
        if instr[1:]:
            if instr[1] in queryModifiers:
                lst.append(queryModifiers[instr[1]])
            else:
                lst.append(instr[1:])
            # ['query', 'length' or number of results]
        else:
            lst.append('3')
        return lst

    instruction = comm[0][0]

    #print(instruction)
    def _right_now_over_me(inst, commands):
        return [_parse_instruction(inst)] + commands

    return _right_now_over_me(instruction, com1)

def mkqlist(actionList):
    compiled = [[a['logic'], a['field'], a['value'], match_fun_list[a['match_fun']]] for a in actionList]
    return compiled

def compile_execute(parse_list):
    whatado = parse_list.pop(0)
    if 'query' in whatado:
        result = sconsult(mkqlist(parse_list))
        mod = whatado[1]
        lngth = len(result)-1
        if 'length' == mod:
            return len(result)
        elif 'all' == mod:
            return result
        else:
            mod = int(mod)
            mod = mod if mod < lngth else lngth
            return result[:mod]


def execute_command(cliString):
    return compile_execute(parse(cliString))

# message discord

def main(cliString):
    return display_all_entries(execute_command(cliString))






bqlist = [
        ['empty', 'head', 'kuo', ssrch],
        ['and', 'body', 'predicate', simple_substring],
        ['or', 'user', 'Ilmen', equality]
        ]

aqlist = [
        ['empty', 'head', 'mui', lambda f, v: re.compile(v).match(f)], 
        ['and', 'body', 'predicate', lambda f, v: v in f],
        ['or', 'user', 'spreadsheet', lambda f, v: re.compile(v).match(f)]
        ]


if __name__ == "__main__":
    print(main(sys.argv[1]))
    
