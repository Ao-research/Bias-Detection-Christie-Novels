# coding: utf-8
######## Semantic Orientation Calculator (SO-CAL) #######
# The code is is majorly from Julian Brooke's code written in 2008
# Changes are made to allow the code running in Python3.5
# The Semantic Orientation Calculator take a properly formated textfile and
# (optionally) a file of span weights and calculates a semantic orietation (SO)
# for the file based on the appearance of words carrying positive or negative
# sentiment, multiplied by weight according to their location in the text
#
# SO-CAL v1.0 (written in perl) supported adjectives, nouns, verbs, adjectives,
# intensification, modals, and negation.
#
# Major Changes since 1.0
# added support for multi-word dictionaries
# added extra weighing of negative phrases
# added lowered weight on (or nullification of) repeated items
# added intensification and nullification based on punctuation
# added intensification based on captialization
# added intensification based on other "highlighting" words
# added clause final intensification for verbs
# added modifier blocking of opposite polarity SO values
# added part-of-speech-specific restricted negation, by word or tag
# added clause boundary words that block backward searches
# added negation-external intensification
# added optional negation shifting limits
# added tag fixing for all_caps words
# added external weighing by use of XML tags
# added weighing based on part of speech
# added external ini file
# added flexible weighing by location in text
# added to the list of irrealis markers (modals)
# added definite determiner overriding of irrealis nullification
# improved handling of "too"
# improved rich output to show calculation
# fixed some small stemming problems
# intensification and negation are now totally separate
#
#
# Changes since V1.11
# merged Spanish and English calculators
# expanded dictionaries
# various minor bug fixes
# XML weighting with real number tags
# added negative negation nullification
# some lists moved to config file
# now uses boundares as indicated by newlines in the input as search
# and sentence boundaries

import operator
import argparse
import os

def get_command_arguments():
    '''
    Read command line input and set values to arguments.
    :return: a list of arguments
    '''
    parser = argparse.ArgumentParser(description='SFU Sentiment Calculator')
    parser.add_argument('--input', '-i', type=str, dest='input', action='store',
                        default='../Sample/output/Preprocessed_Output/BOOKS/no1.txt',
                        help="The input file or folder, and the file should be SO_CAL preprocessed text")

    parser.add_argument('--basicout_path', '-bo', type=str, dest='basicout_path', action='store',
                        default='',
                        help="The basic output")

    parser.add_argument('--richout_path', '-ro', type=str, dest='richout_path', action='store',
                        default='',
                        help="The basic output")

    parser.add_argument('--config', '-c', type=str, dest='config', action='store',
                        default='../Resources/config_files/en_SO_Calc.ini',
                        help="The configuration file for SO-CAL")

    args = parser.parse_args()
    return args

def get_configuration_from_file(configfile):
    config = {}
    for line in configfile.readlines():
        if line:
            line = line.split("#")[0].strip()
            if "=" in line:
                (key, value) = map(str.strip, line.split("="))
                if value.strip():
                    if "[" not in value:
                        if value[-1].isdigit():
                            value = float(value)
                        elif value == "True":
                            value = True
                        elif value == "False":
                            value = False
                        config[key] = value
                    else:
                         elements = value[1:-1].split( ",")
                         if ":" in value:
                             svalues = {}
                             for element in elements:
                                 if element:
                                     (skey,svalue) = map(str.strip, element.split(":"))
                                     if svalue[-1].isdigit():
                                         svalue = float(svalue)
                                     elif svalue == "True":
                                         svalue = True
                                     elif svalue == "False":
                                         svalue = False
                                 svalues[skey] = svalue
                             config[key] = svalues
                         else:
                             config[key] = list(map(str.strip, elements))
    return config

def write_output(output_path, content):
    with open(output_path, "a") as file:
        for line in content:
            file.write(line + "\n")

def same_lists (list1, list2):
    return list1 == list2

def get_multiword_entries (string):
    if "#" in string:
        for item in macro_replace:
            string = string.replace(item, macro_replace[item])
    words = string.split("_")
    entry = []
    keyindex = len(words) - 1
    for index in range(len(words)):
        word = words[index]
        slot = []
        if word[0] == "(":
            slot.append(1)
            slot.append(word[1:-1].split("|"))
            keyindex = index
        elif word[0] == "[":
            ordinality = False
            if word[-1] != "]":
                ordinality = True
            if ordinality:
                slot.append(word[-1])
                word = word[:-1]
            else:
                slot.append(1)
            slot.append(word[1:-1].split("|"))
        else:
            slot = word
        entry.append(slot)
    final_entries = []
    if not isinstance(entry[keyindex], list):
        key = entry[keyindex]
        entry[keyindex] = "#"
        final_entries = [[key,entry]]
    else:
        for key in entry[keyindex][1]:
            final_entry = []
            for index in range(len(entry)):
                if index == keyindex:
                    final_entry.append("#")
                else:
                    final_entry.append(entry[index])
            final_entries.append([key, final_entry])
    return final_entries

def has_accent(word):
    for accent in accents:
        if accent in word:
            return True
    return False

def remove_accents(word):
    for accent in accents:
        word = word.replace(accent, accents[accent])
    return word

def load_dictionary (filepointer, s_dict, c_dict):
    for line in filepointer.readlines():
        pair = line.strip().split()
        if len(pair) == 2:
            if "_" not in pair[0]:
                if language == "Spanish" and has_accent(pair[0]):
                    s_dict[remove_accents(pair[0])] = float(pair[1])
                s_dict[pair[0]] = float(pair[1])
            elif use_multiword_dictionaries:
                entries = get_multiword_entries(pair[0])
                for entry in entries:
                    if entry[0] not in c_dict:
                        c_dict[entry[0]] = [[entry[1], float(pair[1])]]
                    else:
                        c_dict[entry[0]].append([entry[1], float(pair[1])])
    filepointer.close()

def load_extra_dict (filepointer):
    s_dict = False
    c_dict = False
    for line in filepointer.readlines():
        line = line.strip()
        if line:
            if line == "adjectives":
                s_dict = adj_dict
                c_dict = c_adj_dict
            elif line == "nouns":
                s_dict = noun_dict
                c_dict = c_noun_dict
            elif line == "verbs":
                s_dict = verb_dict
                c_dict = c_verb_dict
            elif line == "adverbs":
                s_dict = adv_dict
                c_dict = c_adv_dict
            elif line == "intensifiers":
                s_dict = int_dict
                c_dict = c_adv_dict
            elif s_dict:
                pair = line.split()
                if "_" not in pair[0]:
                    s_dict[pair[0]] = float(pair[1])
                elif use_multiword_dictionaries:
                    entries = get_multiword_entries(pair[0])
                    for entry in entries:
                        if entry[0] not in c_dict:
                            c_dict[entry[0]] = [[entry[1], float(pair[1])]]
                        else:
                             for old_entry in c_dict[entry[0]]:
                                if same_lists(old_entry[0], entry[1]):
                                    c_dict[entry[0]].remove(old_entry)
                             c_dict[entry[0]].append([entry[1], float(pair[1])])
    filepointer.close()

def load_dictionaries ():
    load_dictionary (open (adj_dict_path, encoding = "ISO-8859-1"), adj_dict, c_adj_dict)
    load_dictionary (open (adv_dict_path, encoding = "ISO-8859-1"), adv_dict, c_adv_dict)
    load_dictionary (open (verb_dict_path, encoding = "ISO-8859-1"), verb_dict, c_verb_dict)
    load_dictionary (open (noun_dict_path, encoding = "ISO-8859-1"), noun_dict, c_noun_dict)
    load_dictionary (open (int_dict_path, encoding = "ISO-8859-1"), int_dict, c_int_dict)
    if extra_dict_path:
        load_extra_dict(open (extra_dict_path, encoding = "ISO-8859-1"))
    if simple_SO:
        for s_dict in [adj_dict,adv_dict,verb_dict, noun_dict]:
            for entry in s_dict:
                if s_dict[entry] > 0:
                    s_dict[entry] = 2
                elif s_dict[entry] < 0:
                    s_dict[entry] = -2
        for entry in int_dict:
            if int_dict[entry] > 0:
                int_dict[entry] = .5
            elif int_dict[entry] < 0 and int_dict[entry] > -1:
                int_dict[entry] = -.5
            elif int_dict[entry] < -1:
                int_dict[entry] = -2
        for c_dict in [c_adj_dict,c_adv_dict,c_verb_dict, c_noun_dict]:
            for entry in c_dict:
                for i in range(len(c_dict[entry])):
                    if c_dict[entry][i][1] > 0:
                        c_dict[entry][i] = [c_dict[entry][i][0], 2]
                    elif c_dict[entry][i][1] < 0:
                        c_dict[entry][i] = [c_dict[entry][i][0], -2]
        for entry in c_int_dict:
             for i in range(len(c_int_dict[entry])):
                 if c_int_dict[entry][i][1] > 0:
                     c_int_dict[entry][i] = [c_int_dict[entry][i][0], .5]
                 elif c_int_dict[entry][i][1] < 0 and c_int_dict[entry][i][1] > -1:
                     c_int_dict[entry][i] = [c_int_dict[entry][i][0], -.5]
                 elif c_int_dict[entry][i][1] < -1:
                     c_int_dict[entry][i] = [c_int_dict[entry][i][0], -2]

def convert_fraction(fraction):
    if "/" not in fraction:
        return float(fraction)
    else:
        fraction = fraction.split("/")
        if len(fraction) == 2:
            return float(fraction[0])/float(fraction[1])
    return -1

def is_decimal(string):
    decimal_yet = False
    if len(string) == 0:
        return False
    if string[0] == "-":
        string = string[1:]
        if len(string) == 0:
            return False
    for letter in string:
        if not letter.isdigit():
            if not letter == "." or decimal_yet:
                return False
            else:
                decimal_yet = True
    return True

def convert_ranges():
    new_ranges = []
    for range in weights_by_location:
        pair = range.split("-")
        if len(pair) == 2:
            start = convert_fraction(pair[0].strip())
            end = convert_fraction(pair[1].strip())
            if start >= 0 and start <= 1 and end >= 0 and end <= 1 and start < end:
                new_ranges.append([start,end, weights_by_location[range]])
    return new_ranges

def fill_text_and_weights(infile):
    weight = 1.0
    temp_weight = 1.0
    for line in infile.readlines():
        line = line.replace("<", " <").replace(">", "> ")
        for word in line.strip().split(" "):
            if word:
                if word[0] == "<" and word[-1] == ">":
                    XML_tag = word.strip("<>/")
                    if use_XML_weighing:
                        if XML_tag in weight_tags:
                            weight_modifier = weight_tags[XML_tag]
                        elif is_decimal(XML_tag):
                            weight_modifier = float(XML_tag)
                        else:
                            weight_modifier = 1
                        if word[1] == "/":
                            if weight_modifier != 0:
                                weight /= weight_modifier
                            else:
                                weight = temp_weight
                        else:
                            if weight_modifier != 0:
                                weight *= weight_modifier
                            else:
                                temp_weight = weight
                                weight = 0
                elif "/" in word:
                    text.append(word.split("/"))
                    weights.append(weight)
        boundaries.append(len(text))
    if use_weight_by_location:
        range_dict = convert_ranges()
        for i in range(len(weights)):
            for interval in range_dict:
                if interval[0] <= float(i)/len(weights) and interval[1] > float(i)/len(weights):
                    weights[i] *= interval[2]
    infile.close()

def stem_NN(NN):
    if NN not in noun_dict and NN not in c_noun_dict and  len(NN) > 2 and NN[-1] == "s":
        NN = NN[:-1]
        if NN not in noun_dict and NN not in c_noun_dict and NN[-1] == "e":
            NN = NN[:-1]
            if NN not in noun_dict and NN not in c_noun_dict and NN[-1] == "i":
                NN = NN[:-1] + "y"
    return NN

def stem_VB(VB, type):
    if type == "" or type == "P" or len(VB) < 4 or VB in verb_dict or VB in c_verb_dict:
        return VB
    elif type == "D" or type == "N":
        if VB[-1] == "d":
            VB = VB[:-1]
            if not VB in verb_dict and not VB in c_verb_dict:
                if VB[-1] == "e":
                    VB = VB[:-1]
                if not VB in verb_dict and not VB in c_verb_dict:
                    if VB[-1] == "i":
                        VB = VB[:-1] + "y"
                    elif len(VB) > 1 and VB[-1] == VB[-2]:
                        VB = VB[:-1]
        return VB
    elif type == "G":
        VB = VB[:-3]
        if not VB in verb_dict and not VB in c_verb_dict:
            if len(VB) > 1 and VB[-1] == VB[-2]:
                VB = VB[:-1]
            else:
                VB = VB + "e"
        return VB
    elif type == "Z" and len(VB) > 3:
        if VB[-1] == "s":
            VB = VB[:-1]
            if VB not in verb_dict and not VB in c_verb_dict and VB[-1] == "e":
                VB = VB[:-1]
                if VB not in verb_dict and not VB in c_verb_dict and VB[-1] == "i":
                    VB = VB[:-1] + "y"
        return VB

def stem_RB_to_JJ(RB):
    JJ = RB
    if len(JJ) > 3 and JJ[-2:] == "ly":
        JJ = JJ[:-2]
        if not JJ in adj_dict:
            if JJ + "l" in adj_dict:
                JJ += "l"
            elif JJ + "le" in adj_dict:
                JJ += "le"
            elif JJ[-1] == "i" and JJ[:-1] + "y" in adj_dict:
                JJ = JJ[:-1] + "y"
            elif len(JJ) > 5 and JJ[-2:] == "al" and JJ[:-2] in adj_dict:
                JJ = JJ[:-2]
    return JJ

def stem_ative_adj(JJ):
    if JJ not in adj_dict:
        if JJ + "e" in adj_dict:
            JJ += "e"
        elif JJ[:-1] in adj_dict:
            JJ = JJ[:-1]
        elif JJ[-1] == "i" and JJ[:-1] + "y" in adj_dict:
            JJ = JJ[:-1] + "y"
    return JJ

def stem_comp_JJ(JJ):
    if JJ[-2:] == "er":
        JJ = stem_ative_adj(JJ[:-2])
    return JJ

def stem_super_JJ(JJ):
    if JJ[-3:] == "est":
        JJ = stem_ative_adj(JJ[:-3])
    return JJ

def stem_NC(NC):
    if NC not in noun_dict and len(NC) > 2 and NC[-1] == "s":
        NC = NC[:-1]
    if NC not in noun_dict and NC not in c_noun_dict and len(NC) > 1:
        if NC[-1] == "a":
            NC = NC[:-1] + "o"
        elif NC[-1] == "e":
            NC = NC[:-1]
    return NC

def stem_AQ(AQ):
    if AQ not in adj_dict and len(AQ) > 2 and AQ[-1] == "s":
        AQ = AQ[:-1]
    if AQ not in adj_dict and AQ not in c_adj_dict and len(AQ) > 1:
        if AQ[-1] == "a":
            AQ = AQ[:-1] +  "o"
        elif AQ[-1] == "e":
            AQ = AQ[:-1]
    return AQ

def stem_RG_to_AQ(RG):
    AQ = RG
    if len(AQ) > 6 and AQ[-5:] == "mente":
        AQ = AQ[:-5]
        if not AQ in adj_dict:
            if AQ[-1] == "a":
                AQ = AQ[:-1] + "o"
    return AQ

def stem_super_AQ(AQ):
    if AQ not in adj_dict:
        if len(AQ) > 6 and AQ[-5:] in [chr(237) + "sima", chr(237) + "simo", "isima", "isimo"]:
            AQ = AQ[:-5]
            if AQ not in adj_dict:
                if AQ[-2:] == "qu":
                    AQ = AQ[:-2] + "co"
                elif AQ[-2] == "gu":
                    AQ = AQ[:-1] = "o"
                else:
                    AQ += "o"
    return AQ

def stem_noun(noun):
    if language == "English":
        return stem_NN(noun)
    elif language == "Spanish":
        return stem_NC(noun)

def stem_adv_to_adj(adverb):
    if language == "English":
        return stem_RB_to_JJ(adverb)
    elif language == "Spanish":
        return stem_RG_to_AQ(adverb)

def stem_super_adj(adj):
    if language == "English":
        return stem_super_JJ(adj)
    elif language == "Spanish":
        return stem_super_AQ(adj)

def get_word (pair): return pair[0]
def get_tag (pair) : return pair[1]

def sum_word_counts (word_count_dict):
    count = 0
    for word in word_count_dict:
        count+= word_count_dict[word]
    return count

def find_intensifier(index):
    if index < 0 or index >= len(text) or get_tag(text[index]) == "MOD":
        return False
    if get_word(text[index]).lower() in c_int_dict:
        for word_mod_pair in c_int_dict[get_word(text[index]).lower()]:
            if same_lists(word_mod_pair[0][:-1],map(str.lower, map(get_word,text[index - len(word_mod_pair[0]) + 1:index]))):
                return [len(word_mod_pair[0]), word_mod_pair[1]]
    if get_word(text[index]).lower() in int_dict:
        modifier = int_dict[get_word(text[index]).lower()]
        if get_word(text[index]).isupper() and use_cap_int:
             modifier *= capital_modifier
        return [1, modifier]
    return False

def match_multiword_f(index, words):
    if len (words) == 0:
        return [0, 0]
    else:
        current = words[0]
        if not isinstance(current,list):
            current = [1, [current]]
        if current[0] == "0":
            return match_multiword_f(index, words[1:])
        if current[0] == "*" or current[0] == "?":
            temp = match_multiword_f(index, words[1:])
            if temp[0] != -1:
                return temp
        if index == len(text):
            return [-1, 0]
        match = False
        for word_or_tag in current[1]:
            if word_or_tag.islower():
                match = match or get_word(text[index]).lower() == word_or_tag
            elif word_or_tag.isupper():
                if word_or_tag == "INT":
                    i = 1
                    while index + i < len(text) and text[index + i][0] not in sent_punct:
                        intensifier = find_intensifier(index + i - 1)
                        if intensifier and intensifier[0] == i:
                                result = match_multiword_f(index + i, words[1:])
                                if result[0] != -1:
                                    return [result[0] + i, intensifier[1]]
                        i += 1
                else:
                    match = match or get_tag(text[index]) == word_or_tag
        if not match:
            return [-1, 0]
        else:
            if current[0] == "*":
                temp = match_multiword_f(index + 1, words)
            elif current[0] == "+":
                temp = match_multiword_f(index + 1, [["*", current[1]]] + words[1:])
            elif current[0] == "?":
                temp = match_multiword_f(index + 1, words[1:])
            else:
                temp = match_multiword_f(index + 1, [[str(int(current[0]) - 1), current[1]]] + words[1:])
            if temp[0] == -1:
                return temp
            else:
                return [temp[0] + 1, temp[1]]

def match_multiword_b(index, words):
    if len (words) == 0:
        return [0, 0]
    else:
        current = words[-1]
        if not isinstance(current,list):
            current = [1, [current]]
        if current[0] == "0":
            return match_multiword_b(index, words[:-1])
        if current[0] == "*" or current[0] == "?":
            temp = match_multiword_b(index, words[:-1])
            if temp[0] != -1:
                return temp
        if index == -1:
            return [-1,0]
        match = False
        for word_or_tag in current[1]:
            if word_or_tag.islower():
                match = match or get_word(text[index]).lower() == word_or_tag
            elif word_or_tag.isupper():
                if word_or_tag == "INT":
                    intensifier = find_intensifier(index)
                    if intensifier:
                        i = intensifier[0]
                        result = match_multiword_b(index  - i, words[:-1])
                        if result[0] != -1:
                            return [result[0] + i, intensifier[1]]
                else:
                    match = match or get_tag(text[index]) == word_or_tag
        if not match:
            return [-1, 0]
        else:
            if current[0] == "*":
                temp = match_multiword_b(index - 1, words)
            elif current[0] == "+":
                temp = match_multiword_b(index - 1, words[:-1] + [["*", current[1]]])
            elif current[0] == "?":
                temp = match_multiword_b(index - 1, words[:-1])
            else:
                temp = match_multiword_b(index - 1, words[:-1] + [[str(int(current[0]) - 1), current[1]]])
            if temp[0] == -1:
                return temp
            else:
                return [temp[0] + 1, temp[1]]

def find_multiword(index, dict_entry_list):
    for dict_entry in dict_entry_list:
        words = dict_entry[0]
        SO = dict_entry[1]
        start = words.index("#")
        intensifier = 0
        if start < len(words) - 1:
            (countforward, int_temp) = match_multiword_f(index + 1, words[start +1:])
            if int_temp != 0:
                intensifier = int_temp
        else:
            countforward = 0
        if start > 0:
            (countback, int_temp) = match_multiword_b(index - 1, words[:start])
            if int_temp != 0:
                intensifier = int_temp
        else:
            countback = 0
        if countforward != -1 and countback != -1:
            for i in range(index - countback, index + countforward + 1):
                if get_word(text[i]) in dict_entry[0]:
                    text[i][1] = "MOD"
            return [SO, countback, countforward, intensifier]
    return False

def words_within_num(index, words_tags, num):
    while num > 0:
        if get_word(text[index]) in words_tags or get_tag(text[index]) in words_tags:
            return True
        num -= 1
        index -= 1
    return False

def get_sentence (index):
    sent_start = index
    sent_end = index + 1
    while sent_start > 0 and sent_start not in boundaries:
        sent_start -= 1
    while sent_end < len(text) and sent_end not in boundaries:
        sent_end += 1
    return " ".join(map(get_word, text[sent_start : sent_end]))

def get_sentence_no (index):
    while index not in boundaries:
        index += 1
    return boundaries.index(index)

def get_sent_punct (index):
    while text[index][0] not in sent_punct:
        if index == len(text) - 1:
            return "EOF"
        index += 1
    return get_word(text[index])

def at_boundary (index):
    if index +1 in boundaries:
        return True
    elif use_boundary_punct and get_word(text[index]) in punct:
        return True
    elif use_boundary_words and get_word(text[index]) in boundary_words:
        return True
    else:
        return False

def has_sent_irrealis(index):
    if not (use_definite_assertion and words_within_num(index, definites, 1)):
        while index != -1 and not at_boundary(index):
            if get_word(text[index]).lower() in irrealis:
                return True
            if language == "Spanish":
                tag = get_tag(text[index])
                if len(tag) == 4 and tag[0] == "V" and ((tag[2] == "M" and use_imperative) or (tag[2] == "S" and use_subjunctive) or (tag[3] == "C" and use_conditional)):
                    return True
            index -= 1
    return False

def get_sent_highlighter(index):
    while index != -1 and not at_boundary(index):
        if get_word(text[index]).lower() in highlighters:
            return get_word(text[index]).lower()
        else:
            index -= 1
    return False

def find_negation(index, word_type):
    search = True
    found = -1
    while search and not at_boundary(index) and index != -1:
        current = get_word(text[index]).lower()
        if current in negators:
            search = False
            found = index
        if restricted_neg[word_type] and current not in skipped[word_type] and get_tag(text[index]) not in skipped[word_type]:
            search = False
        index -= 1
    return found

def is_blocker(SO, index):
    if index > -1 and index < len(text) and len(text[index]) == 2:
        (modifier, tag) = text[index]
        if tag == adv_tag and modifier in adv_dict and abs(adv_dict[modifier]) >= blocker_cutoff:
            if abs(SO + adv_dict[modifier]) < abs(SO) + abs(adv_dict[modifier]):
                return True
        elif tag == adj_tag and modifier in adj_dict and abs(adj_dict[modifier]) >= blocker_cutoff:
            if abs(SO + adj_dict[modifier]) < abs(SO) + abs(adj_dict[modifier]):
                return True
        elif tag[:2] == verb_tag and modifier in verb_dict and abs(verb_dict[modifier]) >= blocker_cutoff:
            if abs(SO + verb_dict[modifier]) < abs(SO) + abs(verb_dict[modifier]):
                return True

def find_blocker(SO, index, POS):
    stop = False
    while index > 0 and not stop and not at_boundary(index):
        if len (text[index-1]) == 2:
            (modifier, tag) = text[index-1]
            if is_blocker(SO, index-1):
                return True
            if not modifier in skipped[POS] and not tag[:2] in skipped[POS]:
                stop = True
        index -= 1
    return False

def find_VP_boundary (index):
    while not at_boundary(index) and index < len(text) - 1:
        index += 1
    return index

def is_in_predicate (index):
    while not at_boundary(index) and index > 0:
        index -= 1
        tag = get_tag(text[index])
        if (language == "English" and tag[:2] == "VB" or tag in ["AUX", "AUXG"]) or (language == "Spanish" and tag[0] == "V"):
            return True
    return False

def is_in_imperative (index):
    if get_sent_punct(index) != "?" and not (words_within_num(index, definites, 1)):
        i = index
        while i > -1 and get_word(text[i]) not in sent_punct:
            if at_boundary(index):
                return False
            i -=1
        (word, tag) = text[i+1]
        if (tag == "VBP" or tag == "VB") and word.lower() not in ["were", "was", "am"]:
            return True
    return False

def is_in_quotes (index):
    quotes_left = 0
    quotes_right = 0
    found = False
    current = ""
    i = index
    while current not in sent_punct and i > -1:
        current = get_word(text[i])
        if current == '"' or current == "'":
            quotes_left += 1
        i -= 1
    if operator.mod(quotes_left,2) == 1:
        current = ""
        i = index
        while not found and current not in sent_punct and i < len(text):
            current = get_word(text[i])
            if current == '"' or current == "'":
                quotes_right += 1
            i += 1
        if  (quotes_left - quotes_right == 1) and i < len(text) - 1 and get_word(text[i+1]) == '"':
            quotes_right += 1
        if operator.mod(quotes_right,2) == 1:
            found = True
    return found

def apply_other_modifiers (SO, index, leftedge):
        output = []
        if  use_cap_int and get_word(text[index]).isupper():
            output.append("X " + str(capital_modifier) +  " (CAPITALIZED)")
            SO *= capital_modifier
        if  use_exclam_int and get_sent_punct(index) == "!":
            output.append("X " + str(exclam_modifier) + " (EXCLAMATION)")
            SO *= exclam_modifier
        if  use_highlighters:
            highlighter = get_sent_highlighter(leftedge)
            if highlighter:
                output.append("X " + str(highlighters[highlighter]) + " (HIGHLIGHTED)")
                SO *= highlighters[highlighter]
        if use_quest_mod and get_sent_punct(index) == "?" and not (use_definite_assertion and words_within_num(leftedge, definites, 1)):
            output.append("X 0 (QUESTION)")
            SO = 0
        if language == "English" and use_imperative and is_in_imperative(leftedge):
            output.append("X 0 (IMPERATIVE)")
            SO = 0
        if use_quote_mod and is_in_quotes(index):
            output.append("X 0 (QUOTES)")
            SO = 0
        if  use_irrealis and has_sent_irrealis(leftedge):
            output.append ("X 0 (IRREALIS)")
            SO = 0
        return [SO, output]

def fix_all_caps_English():
    for i in range(0, len(text)):
        if len(text[i]) == 2:
            (word, tag) = text[i]
            if len(word) > 2 and word.isupper() and tag == "NNP":
                word = word.lower()
                if word in adj_dict or word in c_adj_dict:
                    text[i][1] = "JJ"
                elif word in adv_dict or word in c_adv_dict:
                    text[i][1] == "RB"
                else:
                    ex_tag = ""
                    if word[-1] == "s":
                        word = stem_VB(word, "Z")
                        ex_tag = "Z"
                    elif word[-3:] == "ing":
                        word = stem_VB(word, "G")
                        ex_tag = "G"
                    elif word[-2:] == "ed":
                        word = stem_VB(word, "D")
                        ex_tag = "D"
                    if word in verb_dict or word in c_verb_dict:
                        text[i][1] = "VB" + ex_tag

def fix_all_caps_Spanish():
    for i in range(0, len(text)):
        if len(text[i]) == 2:
            (word, tag) = text[i]
            if len(word) > 2 and word.isupper() and tag == "NP":
                word = word.lower()
                alt_word = stem_AQ(word)
                if alt_word in adj_dict or word in c_adj_dict:
                    text[i][1] = "AQ"
                else:
                    alt_word = stem_adv_to_adj(word)
                    if alt_word in adj_dict:
                        text[i][1] == "RG"

def fix_all_caps():
    if language == "English":
        fix_all_caps_English()
    elif language == "Spanish":
        fix_all_caps_Spanish()

def apply_weights (word_SO, index):
    if use_heavy_negation and word_SO < 0:
        word_SO *= neg_multiplier
        if output_calculations:
            richout.write(" X " + str(neg_multiplier) + " (NEGATIVE)")
    word_SO *= weights[index]
    if weights[index] != 1:
        if output_calculations:
            richout.write (" X " + str(weights[index]) + " (WEIGHTED)")
    if output_calculations:
        richout.write (" = " + str(word_SO) + "\n")
    return word_SO

def apply_weights_adv (word_SO, index, output):
    if use_heavy_negation and word_SO < 0:
        word_SO *= neg_multiplier
        if output_calculations:
            output += " X " + str(neg_multiplier) + " (NEGATIVE)"
    word_SO *= weights[index]
    if weights[index] != 1:
        if output_calculations:
            output += " X " + str(weights[index]) + " (WEIGHTED)"
    if output_calculations:
        output += (" = " + str(word_SO) + "\n")
    return [word_SO, output]

def get_noun_SO(index):
    NN = get_word(text[index])
    original_NN = NN
    if NN.isupper():
        NN = NN.lower()
    if get_word(text[index - 1]) in sent_punct:
        NN = NN.lower()
    ntype = get_tag(text[index])[2:]
    NN = stem_noun(NN)
    if NN in c_noun_dict:
        multiword_result = find_multiword(index, c_noun_dict[NN])
    else:
        multiword_result = False
    if NN not in noun_dict and not multiword_result:
        return 0
    else:
        if multiword_result:
            (noun_SO, backcount, forwardcount, int_modifier) = multiword_result
            output = list(map(get_word, text[index - backcount:index + forwardcount + 1]))
            i = index - backcount - 1
        else:
            int_modifier = 0
            output = [original_NN]
            noun_SO = noun_dict[NN]
            i = index - 1
        if use_intensifiers:
            if language == "Spanish":
                intensifier = find_intensifier(index +1)
                if intensifier:
                    int_modifier += intensifier[1]
                    text[index + 1][1] = "MOD"
                    output += [get_word(text[index+1])]
            intensifier = find_intensifier(i)
            if intensifier:
                int_modifier = intensifier[1]
                for j in range (0, intensifier[0]):
                    text[i][1] = "MOD"
                    i -= 1
                output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        negation = find_negation(i, noun_tag)
        if negation != -1:
            output = list(map(get_word, text[negation:i+1])) + output
            if use_intensifiers:
                int_modifier_negex = 0
                i = negation - 1
                if language == "English":
                    while text[i][0] in skipped[adj_tag]:
                        i -= 1
                intensifier = find_intensifier(i)
                if intensifier:
                    int_modifier_negex = intensifier[1]
                    for j in range (0, intensifier[0]):
                        text[i][1] = "MOD"
                        i -= 1
                    output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        output.append(str(noun_SO))
        if int_modifier != 0:
            noun_SO = noun_SO *(1+int_modifier)
            output.append("X " + str(1 + int_modifier) + " (INTENSIFIED)")
        elif use_blocking and find_blocker(noun_SO, index, noun_tag):
            output.append("X 0 (BLOCKED)")
            noun_SO = 0
        if use_negation and negation != -1:
            if neg_negation_nullification and noun_SO < 0:
                neg_shift = abs(noun_SO)
            elif polarity_switch_neg or (limit_shift and abs(noun_SO) * 2 < noun_neg_shift):
                neg_shift = abs(noun_SO) * 2
            else:
                neg_shift = noun_neg_shift
            if noun_SO > 0:
                noun_SO -= neg_shift
                output.append ("- "+ str(neg_shift))
            elif noun_SO < 0:
                noun_SO += neg_shift
                output.append ("+ "+ str(neg_shift))
            output.append("(NEGATED)")
            if use_intensifiers and int_modifier_negex != 0:
                noun_SO *=(1+int_modifier_negex)
                output.append("X " + str(1 + int_modifier_negex) + " (INTENSIFIED)")
        (noun_SO, new_out) = apply_other_modifiers(noun_SO, index, i)
        output += new_out
        if noun_SO != 0:
            if int_modifier != 0 and int_multiplier != 1:
                noun_SO *= int_multiplier
                output.append("X " + str(int_multiplier) + " (INT_WEIGHT)")
            if NN not in word_counts[0]:
                word_counts[0][NN] = 1
            else:
                word_counts[0][NN] += 1
                if negation == -1:
                    if use_word_counts_lower:
                        noun_SO /= word_counts[0][NN]
                        output.append("X 1/" + str(word_counts[0][NN]) + " (REPEATED)")
                    if use_word_counts_block:
                        noun_SO = 0
                        output.append("X 0 (REPEATED)")
        if noun_multiplier != 1:
            noun_SO *= noun_multiplier
            output.append("X " + str(noun_multiplier) + " (NOUN)")
        if output_calculations:
            for word in output:
                richout.write(word + " ")
        if output_calculations and noun_SO == 0:
            richout.write("= 0\n")
        return noun_SO

def get_verb_SO(index):
    VB = get_word(text[index])
    original_VB = VB
    if VB.isupper():
        VB = VB.lower()
    if get_word(text[index - 1]) in sent_punct:
        VB = VB.lower()
    if language == "English":
        vtype = get_tag(text[index])[2:]
        VB = stem_VB(VB, vtype)
    if VB in c_verb_dict:
        multiword_result = find_multiword(index, c_verb_dict[VB])
    else:
        multiword_result = False
    if VB in not_wanted_verb:
        return 0
    elif VB not in verb_dict and not multiword_result:
        return 0
    else:
        if multiword_result:
            (verb_SO, backcount, forwardcount, int_modifier) = multiword_result
            output = list(map(get_word, text[index - backcount:index + forwardcount + 1]))
            i = index - backcount - 1
        else:
            int_modifier = 0
            output = [original_VB]
            verb_SO = verb_dict[VB]
            i = index - 1
        if use_intensifiers:
            intensifier = find_intensifier(i)
            if intensifier:
                int_modifier += intensifier[1]
                for j in range (0, intensifier[0]):
                    text[i][1] = "MOD"
                    i -= 1
                output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
            if use_clause_final_int:
                edge = find_VP_boundary(index)
                intensifier = find_intensifier(edge - 1)
                if intensifier:
                    int_modifier = intensifier[1]
                    for j in range (0, intensifier[0]):
                        text[edge - 1 - j][1] = "MOD"
                    output = output + list(map(get_word, text[index + 1: edge]))
        negation = find_negation(i, verb_tag)
        if negation != -1:
            output = list(map(get_word, text[negation:i+1])) + output
            if use_intensifiers:
                int_modifier_negex = 0
                i = negation - 1
                if language == "English":
                    while text[i][0] in skipped["JJ"]:
                        i -= 1
                intensifier = find_intensifier(i)
                if intensifier:
                    int_modifier_negex = intensifier[1]
                    for j in range (0, intensifier[0]):
                        text[i][1] = "MOD"
                        i -= 1
                    output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        output.append(str(verb_SO))
        if int_modifier != 0:
            verb_SO = verb_SO *(1+int_modifier)
            output.append("X " + str(1 + int_modifier) + " (INTENSIFIED)")
        elif use_blocking and find_blocker(verb_SO, index, verb_tag):
            output.append("X 0 (BLOCKED)")
            verb_SO = 0
        if use_negation and negation != -1:
            if neg_negation_nullification and verb_SO < 0:
                neg_shift = abs(verb_SO)
            elif polarity_switch_neg or (limit_shift and abs(verb_SO) * 2 < verb_neg_shift):
                neg_shift = abs(verb_SO) * 2
            else:
                neg_shift = verb_neg_shift
            if verb_SO > 0:
                verb_SO -= neg_shift
                output.append ("- "+ str(neg_shift))
            elif verb_SO < 0:
                verb_SO += neg_shift
                output.append("+ " + str(neg_shift))
            output.append("(NEGATED)")
            if use_intensifiers and int_modifier_negex != 0:
                verb_SO *=(1+int_modifier_negex)
                output.append("X " + str(1 + int_modifier_negex) + " (INTENSIFIED)")
        (verb_SO, new_out) = apply_other_modifiers(verb_SO, index, i)
        output += new_out
        if verb_SO != 0:
            if int_modifier != 0 and int_multiplier != 1:
                verb_SO *= int_multiplier
                output.append("X " + str(int_multiplier) + " (INT_WEIGHT)")
            if VB not in word_counts[1]:
                word_counts[1][VB] = 1
            else:
                word_counts[1][VB] += 1
                if negation == -1:
                    if use_word_counts_lower:
                        verb_SO /= word_counts[1][VB]
                        output.append("X 1/" + str(word_counts[1][VB]) + " (REPEATED)")
                    if use_word_counts_block:
                        verb_SO = 0
                        output.append("X 0 (REPEATED)")
        if verb_multiplier != 1:
            verb_SO *= verb_multiplier
            output.append("X " + str(verb_multiplier) + " (VERB)")
        if output_calculations:
            for word in output:
                richout.write(word + " ")
        if output_calculations and verb_SO == 0:
            richout.write("= 0\n")
        return verb_SO

def get_adj_SO(index):
    JJ = get_word(text[index])
    original_JJ = JJ
    if JJ.isupper():
        JJ = JJ.lower()
    if get_word(text[index - 1]) in sent_punct:
        JJ = JJ.lower()
    if language == "English":
        jtype = get_tag(text[index])[2:]
        if jtype == "R":
            JJ = stem_comp_JJ(JJ)
        elif jtype == "S":
            JJ = stem_super_JJ(JJ)
    else:
        jtype = get_tag(text[index])[2:3]
        if jtype == "S":
            JJ = stem_super_AQ(JJ)
        elif jtype == "C":
            if JJ[-4:] == "ador":
                if JJ[:-4] + "ador" in adj_dict:
                    JJ = JJ[:-4] + "ador"
                else:
                    JJ = JJ[:-4] + "ar"
            else:
                JJ = stem_AQ(JJ)
    if JJ in c_adj_dict:
        multiword_result = find_multiword(index, c_adj_dict[JJ])
    else:
        multiword_result = False
    if JJ not in adj_dict and not multiword_result:
        return 0
    else:
        if multiword_result:
            (adj_SO, backcount, forwardcount, int_modifier) = multiword_result
            output = list(map(get_word, text[index - backcount:index + forwardcount + 1]))
            i = index - backcount - 1
        else:
            int_modifier = 0
            output = [original_JJ]
            adj_SO = adj_dict[JJ]
            i = index - 1
        if use_intensifiers:
            intensifier = find_intensifier(i)
            if intensifier:
                int_modifier += intensifier[1]
                for j in range (0, intensifier[0]):
                    text[i][1] = "MOD"
                    i -= 1
                output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        negation = find_negation(i, adj_tag)
        if negation != -1:
            output = list(map(get_word, text[negation:i+1])) + output
            if use_intensifiers:
                int_modifier_negex = 0
                i = negation - 1
                intensifier = find_intensifier(i)
                if intensifier:
                    int_modifier_negex = intensifier[1]
                    for j in range (0, intensifier[0]):
                        text[i][1] = "MOD"
                        i -= 1
                    output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        output.append(str(adj_SO))
        if int_modifier != 0:
            adj_SO = adj_SO *(1+int_modifier)
            output.append("X " + str(1 + int_modifier) + " (INTENSIFIED)")
        elif use_blocking and find_blocker(adj_SO, index, adj_tag):
            output.append("X 0 (BLOCKED)")
            adj_SO = 0
        if use_negation and negation != -1:
            if neg_negation_nullification and adj_SO < 0:
                neg_shift = abs(adj_SO)
            elif polarity_switch_neg or (limit_shift and abs(adj_SO) * 2 < adj_neg_shift):
                neg_shift = abs(adj_SO) * 2
            else:
                neg_shift = adj_neg_shift
            if adj_SO > 0:
                adj_SO -= neg_shift
                output.append ("- "+ str(neg_shift))
            elif adj_SO < 0:
                adj_SO += neg_shift
                output.append ("+ "+ str(neg_shift))
            output.append("(NEGATED)")
            if use_intensifiers and int_modifier_negex != 0:
                adj_SO *=(1+int_modifier_negex)
                output.append("X " + str(1 + int_modifier_negex) + " (INTENSIFIED)")
        (adj_SO, new_out) = apply_other_modifiers(adj_SO, index, i)
        output += new_out
        if adj_SO != 0:
            if int_modifier != 0 and int_multiplier != 1:
                adj_SO *= int_multiplier
                output.append("X " + str(int_multiplier) + " (INT_WEIGHT)")
            if JJ not in word_counts[2]:
                word_counts[2][JJ] = 1
            else:
                word_counts[2][JJ] += 1
                if negation == -1:
                    if use_word_counts_lower:
                        adj_SO /= word_counts[2][JJ]
                        output.append("X 1/" + str(word_counts[2][JJ]) + " (REPEATED)")
                    if use_word_counts_block:
                        adj_SO = 0
                        output.append("X 0 (REPEATED)")
        if adj_multiplier != 1:
            adj_SO *= adj_multiplier
            output.append("X " + str(adj_multiplier) + " (ADJECTIVE)")
        if output_calculations:
            for word in output:
                richout.write(word + " ")
        if output_calculations and adj_SO == 0:
            richout.write("= 0\n")
        return adj_SO

def get_adv_SO(index):
    RB = get_word(text[index])
    original_RB = RB
    if RB.isupper():
        RB = RB.lower()
    if get_word(text[index - 1]) in sent_punct:
        RB = RB.lower()
    if language == "English":
        if get_tag(text[index])[2:] == "R":
            JJ = stem_RB_to_JJ(RB)
            if JJ in adj_dict:
                adj_output = [original_RB]
                adj_SO = adj_dict[JJ]
                adj_output.append(str(adj_SO))
                negation = find_negation(index - 1, adj_tag)
                if negation != -1:
                    adj_output = list(map(get_word, text[negation:index])) + adj_output
                if use_negation and negation != -1:
                    if neg_negation_nullification and adj_SO < 0:
                        neg_shift = abs(adj_SO)
                    elif polarity_switch_neg or (limit_shift and abs(adj_SO) * 2 < adj_neg_shift):
                        neg_shift = abs(adj_SO) * 2
                    else:
                        neg_shift = adj_neg_shift
                    if adj_SO > 0:
                        adj_SO -= neg_shift
                        adj_output.append ("- "+ str(neg_shift))
                    elif adj_SO < 0:
                        adj_SO += neg_shift
                        adj_output.append ("+ "+ str(neg_shift))
                    adj_output.append("(NEGATED)")
                (adj_SO, new_out) = apply_other_modifiers(adj_SO, index, index)
                adj_output += new_out
                if adj_SO != 0:
                    if adj_multiplier != 1:
                        adj_SO *= adj_multiplier
                        adj_output.append("X " + str(adj_multiplier) + " (ADJECTIVE)")
                if output_calculations:
                    for word in adj_output:
                        richout.write(word + " ")
                return adj_SO
        if RB in c_adv_dict:
            multiword_result = find_multiword(index, c_adv_dict[RB])
        else:
            multiword_result = False
    elif language == "Spanish":
        RB = stem_adv_to_adj(RB)
        if RB in c_adv_dict:
            multiword_result = find_multiword(index, c_adv_dict[RB])
        else:
            multiword_result = False
    if RB not in adv_dict and not multiword_result:
        return 0
    else:
        if multiword_result:
            (adv_SO, backcount, forwardcount, int_modifier) = multiword_result
            output = list(map(get_word, text[index - backcount:index + forwardcount + 1]))
            i = index - backcount - 1
        else:
            int_modifier = 0
            output = [original_RB]
            adv_SO = adv_dict[RB]
            i = index - 1
        if use_intensifiers:
            intensifier = find_intensifier(i)
            if intensifier:
                int_modifier += intensifier[1]
                for j in range (0, intensifier[0]):
                    text[i][1] = "MOD"
                    i -= 1
                output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        negation = find_negation(i, adv_tag)
        if negation != -1:
            output = list(map(get_word, text[negation:i+1])) + output
            if use_intensifiers:
                int_modifier_negex = 0
                i = negation - 1
                intensifier = find_intensifier(i)
                if intensifier:
                    int_modifier_negex = intensifier[1]
                    for j in range (0, intensifier[0]):
                        text[i][1] = "MOD"
                        i -= 1
                    output = list(map(get_word, text[i + 1:i + intensifier[0] + 1])) + output
        output.append(str(adv_SO))
        if int_modifier != 0:
            adv_SO = adv_SO *(1+int_modifier)
            output.append("X " + str(1 + int_modifier) + " (INTENSIFIED)")
        elif use_blocking and find_blocker(adv_SO, index, adv_tag):
            output.append("X 0 (BLOCKED)")
            adv_SO = 0
        if use_negation and negation != -1:
            if neg_negation_nullification and adv_SO < 0:
                neg_shift = abs(adv_SO)
            elif polarity_switch_neg or (limit_shift and abs(adv_SO) * 2 < adv_neg_shift):
                neg_shift = abs(adv_SO) * 2
            else:
                neg_shift = adv_neg_shift
            if adv_SO > 0:
                adv_SO -= neg_shift
                output.append ("- "+ str(neg_shift))
            elif adv_SO < 0:
                adv_SO += neg_shift
                output.append ("+ "+ str(neg_shift))
            output.append("(NEGATED)")
        (adv_SO, new_out) = apply_other_modifiers(adv_SO, index, i)
        output += new_out
        if adv_SO != 0:
            if int_modifier != 0 and int_multiplier != 1:
                adv_SO *= int_multiplier
                output.append("X " + str(int_multiplier) + " (INT_WEIGHT)")
            if RB not in word_counts[3]:
                word_counts[3][RB] = 1
            else:
                word_counts[3][RB] += 1
                if negation == -1:
                    if use_word_counts_lower:
                        adv_SO /= word_counts[3][RB]
                        output.append("X 1/" + str(word_counts[3][RB]) + " (REPEATED)")
                    if use_word_counts_block:
                        adv_SO = 0
                        output.append("X 0 (REPEATED)")
        if adv_multiplier != 1:
            adv_SO *= adv_multiplier
            output.append("X " + str(adv_multiplier) + " (ADVERB)")
        if output_calculations:
            for word in output:
                richout.write(word + " ")
        if output_calculations and adv_SO == 0:
            richout.write("= 0\n")
        return adv_SO

def get_other_SO(index):
    word = get_word(text[index])
    if word.lower() in extra_dict:
        word_SO = extra_dict[word.lower()]
        output = [word]
        output.append(str(word_SO))
        negation = find_negation(index - 1, "OTHER")
        if negation != -1:
            output = list(map(get_word, text[negation:index])) + output
        if use_negation and negation != -1:
            if neg_negation_nullification and word_SO < 0:
                neg_shift = abs(word_SO)
            elif polarity_switch_neg or (limit_shift and abs(word_SO) * 2 < adj_neg_shift):
                neg_shift = abs(word_SO) * 2
            else:
                neg_shift = adj_neg_shift
            if word_SO > 0:
                word_SO -= neg_shift
                output.append ("- "+ str(neg_shift))
            elif word_SO < 0:
                word_SO += neg_shift
                output.append ("+ "+ str(neg_shift))
            output.append("(NEGATED)")
        (word_SO, new_out) = apply_other_modifiers(word_SO, index, index)
        output += new_out
        if output_calculations:
            for word in output:
                richout.write(word + " ")
        return word_SO
    return 0

def get_phrase_SO(index):
    tag = get_tag(text[index])
    if tag[:2] == noun_tag:
        word_SO = get_noun_SO(index)
    elif tag[:2] == verb_tag:
        word_SO = get_verb_SO(index)
    elif tag == adj_tag:
        word_SO = get_adj_SO(index)
    elif tag == adv_tag:
        word_SO = get_adv_SO(index)
    else:
        word_SO = get_other_SO(index)
    return word_SO

def main():
    args = get_command_arguments()

    global language
    global word_counts
    global adj_dict, noun_dict, verb_dict, adv_dict, int_dict
    global c_adj_dict, c_noun_dict, c_verb_dict, c_adv_dict, c_int_dict
    global text, boundaries, weights
    global punct, sent_punct
    global extra_dict_path, extra_dict, weight_tags
    global use_XML_weighing, use_weight_by_location, weights_by_location
    global use_multiword_dictionaries, macro_replace, language
    global output_calculations, simple_SO, output_type
    global noun_tag, adj_tag, adv_tag, verb_tag
    global use_negation, noun_neg_shift, verb_neg_shift, adj_neg_shift, adv_neg_shift, polarity_switch_neg, limit_shift, neg_negation_nullification, use_heavy_negation, neg_multiplier
    global blocked, restricted_neg, skipped, use_blocking, blocker_cutoff
    global use_cap_int, capital_modifier, use_exclam_int, exclam_modifier
    global int_multiplier, int_tags, int_types, int_dict, use_intensifiers
    global highlighters, use_highlighters, use_clause_final_int
    global use_quest_mod, use_definite_assertion, definites, use_imperative, use_quote_mod, use_irrealis
    global use_boundary_punct, use_boundary_words, boundary_words

    word_counts = [{},{},{},{}]
    config = get_configuration_from_file(open(args.config, encoding = "ISO-8859-1"))

    if "Language" in config:
        language = config["Language"]
    else:
        language = "English"

    adj_dict = {}
    noun_dict = {}
    verb_dict = {}
    adv_dict = {}
    int_dict = {}
    c_adj_dict = {}
    c_noun_dict = {}
    c_verb_dict = {}
    c_adv_dict = {}
    c_int_dict = {}
    text = []
    boundaries = []
    weights = []

    punct = [",", ";", ":", ".", "!", "?"]
    sent_punct = [".", "!", "?"]
    extra_dict_path = False
    extra_dict = {}
    weight_tags = {}

    use_XML_weighing = False
    use_weight_by_location = False
    weights_by_location = {}

    use_multiword_dictionaries = False
    macro_replace = {}
    language = "English"
    output_calculations = False
    simple_SO = False
    output_type = "SIMPLE"

    noun_tag = "NN"
    adj_tag = "JJ"
    adv_tag = "RB"
    verb_tag = "VB"

    use_negation = False
    noun_neg_shift = 0
    verb_neg_shift = 0
    adj_neg_shift = 0
    adv_neg_shift = 0
    polarity_switch_neg = False
    limit_shift = False
    neg_negation_nullification = False
    use_heavy_negation = False
    neg_multiplier = 1

    blocked = []
    restricted_neg = {}
    skipped = {}
    use_blocking = False
    blocker_cutoff = 1.0

    use_cap_int = False
    capital_modifier = 1
    use_exclam_int = False
    exclam_modifier = 1

    int_multiplier = 1
    int_tags = []
    int_types = []
    int_dict = {}
    use_intensifiers = False

    highlighters = {}
    use_highlighters = False
    use_clause_final_int = False

    use_quest_mod = False
    use_definite_assertion = False
    definites = []
    use_imperative = False
    use_quote_mod = False
    use_irrealis = False

    use_boundary_punct = False
    use_boundary_words = False
    boundary_words = []

    if "use_negation" in config and config["use_negation"]:
        use_negation = True

        if "negators" in config:
            negators = config["negators"]
        else:
            negators = ["not", "n't", "never", "no"]

        if "noun_neg_shift" in config:
            noun_neg_shift = config["noun_neg_shift"]
        if "verb_neg_shift" in config:
            verb_neg_shift = config["verb_neg_shift"]
        if "adj_neg_shift" in config:
            adj_neg_shift = config["adj_neg_shift"]
        if "adv_neg_shift" in config:
            adv_neg_shift = config["adv_neg_shift"]
        if "polarity_switch_neg" in config:
            polarity_switch_neg = config["polarity_switch_neg"]
        if "limit_shift" in config:
            limit_shift = config["limit_shift"]
        if "neg_negation_nullification" in config:
            neg_negation_nullification = config["neg_negation_nullification"]
        if "use_heavy_negation" in config:
            use_heavy_negation = config["use_heavy_negation"]
        if "neg_multiplier" in config:
            neg_multiplier = config["neg_multiplier"]

        if "noun_block" in config:
            blocked.append("NN")
        if "adj_block" in config:
            blocked.append("JJ")
        if "verb_block" in config:
            blocked.append("VB")
        if "adv_block" in config:
            blocked.append("RB")
        if "use_blocking" in config:
            use_blocking = True
        if "blocker_cutoff" in config:
            blocker_cutoff = config["blocker_cutoff"]

        restricted_neg["NN"] = []
        restricted_neg["JJ"] = []
        restricted_neg["VB"] = []
        restricted_neg["RB"] = []

        if "use_noun_restrictions" in config:
            for word in config["noun_restrictions"]:
                if word[0] == "!" or word.isupper():
                    restricted_neg["NN"].append(word)
                else:
                    restricted_neg["NN"].append(word.lower())

        if "use_verb_restrictions" in config:
            for word in config["verb_restrictions"]:
                if word[0] == "!" or word.isupper():
                    restricted_neg["VB"].append(word)
                else:
                    restricted_neg["VB"].append(word.lower())

        if "use_adj_restrictions" in config:
            for word in config["adj_restrictions"]:
                if word[0] == "!" or word.isupper():
                    restricted_neg["JJ"].append(word)
                else:
                    restricted_neg["JJ"].append(word.lower())

        if "use_adv_restrictions" in config:
            for word in config["adv_restrictions"]:
                if word[0] == "!" or word.isupper():
                    restricted_neg["RB"].append(word)
                else:
                    restricted_neg["RB"].append(word.lower())

    if "use_multiword_dictionaries" in config:
        use_multiword_dictionaries = True

        if "macro_replace" in config:
            macro_replace = config["macro_replace"]

    if "use_XML_weighing" in config and config["use_XML_weighing"]:
        use_XML_weighing = True
        if "weight_tags" in config:
            weight_tags = config["weight_tags"]

    if "use_weight_by_location" in config and config["use_weight_by_location"]:
        use_weight_by_location = True
        if "weights_by_location" in config:
            weights_by_location = config["weights_by_location"]

    if "extra_dict" in config:
        extra_dict_path = config["extra_dict"]
    if "simple_SO" in config:
        simple_SO = config["simple_SO"]
    if "output_calculations" in config:
        output_calculations = config["output_calculations"]

    if "use_cap_int" in config:
        use_cap_int = config["use_cap_int"]
    if "capital_modifier" in config:
        capital_modifier = config["capital_modifier"]
    if "use_exclam_int" in config:
        use_exclam_int = config["use_exclam_int"]
    if "exclam_modifier" in config:
        exclam_modifier = config["exclam_modifier"]
    if "use_highlighters" in config:
        use_highlighters = config["use_highlighters"]
    if "highlighters" in config:
        highlighters = config["highlighters"]
    if "use_clause_final_int" in config:
        use_clause_final_int = config["use_clause_final_int"]

    if "int_multiplier" in config:
        int_multiplier = config["int_multiplier"]
    if "use_intensifiers" in config:
        use_intensifiers = config["use_intensifiers"]
    if "int_tags" in config:
        int_tags = config["int_tags"]
    if "int_types" in config:
        int_types = config["int_types"]
    if "int_dict" in config:
        int_dict = config["int_dict"]

    if "output_type" in config:
        output_type = config["output_type"]
    if "use_quest_mod" in config:
        use_quest_mod = config["use_quest_mod"]
    if "use_definite_assertion" in config:
        use_definite_assertion = config["use_definite_assertion"]
    if "definites" in config:
        definites = config["definites"]
    if "use_imperative" in config:
        use_imperative = config["use_imperative"]
    if "use_quote_mod" in config:
        use_quote_mod = config["use_quote_mod"]
    if "use_irrealis" in config:
        use_irrealis = config["use_irrealis"]

    if "use_boundary_punct" in config:
        use_boundary_punct = config["use_boundary_punct"]
    if "use_boundary_words" in config:
        use_boundary_words = config["use_boundary_words"]
    if "boundary_words" in config:
        boundary_words = config["boundary_words"]

    adj_dict_path = config["adj_dict"]
    verb_dict_path = config["verb_dict"]
    noun_dict_path = config["noun_dict"]
    adv_dict_path = config["adv_dict"]
    int_dict_path = config["int_dict"]
    use_boundary_words = False

    load_dictionaries()
    fix_all_caps()
    input_path = args.input

    if os.path.isfile(input_path):
        process_file(input_path, args.basicout_path, args.richout_path)
    else:
        for filename in os.listdir(input_path):
            process_file(os.path.join(input_path, filename), args.basicout_path, args.richout_path)

def process_file(input_path, basicout_path, richout_path):
    global text, boundaries, weights, output_calculations, richout

    text = []
    boundaries = []
    weights = []

    input_file = open(input_path, encoding = "ISO-8859-1")
    fill_text_and_weights(input_file)
    input_file.close()

    SO_value = 0
    num_clauses = 0

    if output_calculations:
        richout = open(richout_path, "w", encoding="utf-8")
    output_lines = []
    for i in range(0, len(text)):
        word_SO = get_phrase_SO(i)
        if word_SO != 0:
            num_clauses += 1
            if output_calculations:
                richout.write("SO = " + str(SO_value))
            word_SO = apply_weights(word_SO, i)
            SO_value += word_SO
        if output_calculations:
            richout.write("\n")

    if output_calculations:
        richout.close()

    output_lines.append("Semantic Orientation: " + str(SO_value))
    output_lines.append("Number of clauses: " + str(num_clauses))
    write_output(basicout_path, output_lines)

if __name__ == "__main__":
    main()
