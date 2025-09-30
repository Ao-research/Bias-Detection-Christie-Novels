import operator
import argparse
import os

def get_command_arguments():
    parser = argparse.ArgumentParser(description='SFU Sentiment Calculator')
    parser.add_argument('--input', '-i', type=str, dest='input', required=True,
                        help="包含SO_CAL预处理文本文件的输入文件夹")
    parser.add_argument('--output', '-o', type=str, dest='output', required=True,
                        help="存储所有情感分数的输出文件")
    parser.add_argument('--config', '-c', type=str, dest='config', required=True,
                        help="SO-CAL的配置文件")
    parser.add_argument('--dic_folder', '-d', type=str, dest='dic_folder', required=True,
                        help="包含所有词典文件的文件夹")
    args = parser.parse_args()
    return args

args = get_command_arguments()
configfile = open(args.config, "r")
basicout = open(args.output, "w")

config = {}

def get_configuration_from_file():
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
                         elements = value[1:-1].split(",")
                         if ":" in value:
                             svalues = {}
                             for element in elements:
                                 if element:
                                     (skey, svalue) = map(str.strip, element.split(":"))
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
    configfile.close()

get_configuration_from_file()

# 加载配置设置
language = config["language"]
use_adjectives = config["use_adjectives"]
use_nouns = config["use_nouns"]
use_verbs = config["use_verbs"]
use_adverbs = config["use_adverbs"]
use_intensifiers = config["use_intensifiers"]
use_negation = config["use_negation"]
use_comparatives = config["use_comparatives"]
use_superlatives = config["use_superlatives"]
use_multiword_dictionaries = config["use_multiword_dictionaries"]
use_extra_dict = config["use_extra_dict"]
use_XML_weighing = config["use_XML_weighing"]
use_weight_by_location = config["use_weight_by_location"]
use_irrealis = config["use_irrealis"]
use_subjunctive = config["use_subjunctive"]
use_imperative = config["use_imperative"]
use_conditional = config["use_conditional"]
use_highlighters = config["use_highlighters"]
use_cap_int = config["use_cap_int"]
fix_cap_tags = config["fix_cap_tags"]
use_exclam_int = config["use_exclam_int"]
use_quest_mod = config["use_quest_mod"]
use_quote_mod = config["use_quote_mod"]
use_definite_assertion = config["use_definite_assertion"]
use_clause_final_int = config["use_clause_final_int"]
use_heavy_negation = config["use_heavy_negation"]
use_word_counts_lower = config["use_word_counts_lower"]
use_word_counts_block = config["use_word_counts_block"]
use_blocking = config["use_blocking"]
adv_learning = config["adv_learning"]
limit_shift = config["limit_shift"]
neg_negation_nullification = config["neg_negation_nullification"]
polarity_switch_neg = config["polarity_switch_neg"]
restricted_neg = config["restricted_neg"]
simple_SO = config["simple_SO"]
use_boundary_words = config["use_boundary_words"]
use_boundary_punct = config["use_boundary_punctuation"]

# 修饰符
adj_multiplier = config["adj_multiplier"]
adv_multiplier = config["adv_multiplier"]
verb_multiplier = config["verb_multiplier"]
noun_multiplier = config["noun_multiplier"]
int_multiplier = config["int_multiplier"]
neg_multiplier = config["neg_multiplier"]
capital_modifier = config["capital_modifier"]
exclam_modifier = config["exclam_modifier"]
verb_neg_shift = config["verb_neg_shift"]
noun_neg_shift = config["noun_neg_shift"]
adj_neg_shift = config["adj_neg_shift"]
adv_neg_shift = config["adv_neg_shift"]
blocker_cutoff = config["blocker_cutoff"]

# 词典
dic_dir = config["dic_dir"]
adj_dict_path = dic_dir + config["adj_dict"]
adv_dict_path = dic_dir + config["adv_dict"]
noun_dict_path = dic_dir + config["noun_dict"]
verb_dict_path = dic_dir + config["verb_dict"]
int_dict_path = dic_dir + config["int_dict"]
if use_extra_dict and config["extra_dict"]:
    extra_dict_path = dic_dir + config["extra_dict"]
else:
    extra_dict_path = False

adj_dict = {} # 简单（单词）词典
adv_dict = {}
noun_dict = {}
verb_dict = {}
int_dict = {}
c_adj_dict = {} # 复杂（多词）词典
c_adv_dict = {}
c_noun_dict = {}
c_verb_dict = {}
c_int_dict = {}
new_adv_dict = {}

# 文本
text = [] # 文本是单词和标签的列表
weights = [] # 权重应该与文本长度相同，每个词一个
word_counts = [{}, {}, {}, {}] # 跟踪文本中每个词条出现的次数
text_SO = 0 # 所有词的SO值之和
SO_counter = 0 # 具有SO值的词的计数
boundaries = [] # 输入中的换行边界位置

# 内部词汇列表
if language == "English":
    not_wanted_adj = ["other", "same", "such", "first", "next", "last", "few", "many", "less", "more", "least", "most"]
    not_wanted_adv = [ "really", "especially", "apparently", "actually", "evidently", "suddenly", "completely","honestly", "basically", "probably", "seemingly", "nearly", "highly", "exactly", "equally", "literally", "definitely", "practically", "obviously", "immediately", "intentionally", "usually", "particularly", "shortly", "clearly", "mildly", "sincerely", "accidentally", "eventually", "finally", "personally", "importantly", "specifically", "shortly", "clearly", "mildly", "sincerely", "accidentally", "eventually", "finally", "personally", "importantly", "specifically", "likely", "absolutely", "necessarily", "strongly", "relatively", "comparatively", "entirely", "possibly", "generally", "expressly", "ultimately", "originally", "initially", "virtually", "technically", "frankly", "seriously", "fairly",  "approximately", "critically", "continually", "certainly",  "regularly", "essentially", "lately", "explicitly", "right", "subtly",  "lastly", "vocally", "technologically", "firstly", "tally", "ideally", "specially", "humanly", "socially", "sexually", "preferably", "immediately", "legally", "hopefully", "largely", "frequently", "factually", "typically"]
    not_wanted_verb = []
    negators = ["not", "no", "n't", "neither", "nor", "nothing", "never", "none", "lack", "lacked", "lacking", "lacks", "missing", "without", "absence", "devoid"]
    punct = [".", ",", ";", "!", "?", ":", ")", "(", "\"", "'", "-"]
    sent_punct = [".", ";", "!", "?", ":", "\n", "\r"]
    skipped = {"JJ": ["even", "to", "being", "be", "been", "is", "was", "'ve", "have", "had", "do", "did", "done", "of", "as", "DT", "PSP$"], "RB": ["VB", "VBZ", "VBP", "VBG"], "VB":["TO", "being", "been", "be"], "NN":["DT", "JJ", "NN", "of", "have", "has", "come", "with", "include"]}
    comparatives = ["less", "more", "as"]
    superlatives = ["most", "least"]
    definites = ["the","this", "POS", "PRP$"]
    noun_tag = "NN"
    verb_tag = "VB"
    adj_tag = "JJ"
    adv_tag = "RB"
    macro_replace = {"#NP?#": "[PDT]?_[DET|PRP|PRP$|NN|NNP]?_[POS]?_[NN|NNP|JJ]?_[NN|NNP|NNS|NNPS]?", "#PER?#": "[me|us|her|him]?", "#give#": "give|gave|given", "#fall#": "fall|fell|fallen", "#get#": "get|got|gotten", "#come#": "come|came", "#go#": "go|went|gone", "#show#": "show|shown", "#make#": "make|made", "#hang#": "hang|hung", "#break#": "break|broke|broken", "#see#": "see|saw|seen", "#be#": "be|am|are|was|were|been", "#bring#": "bring|brought", "#think#" : "think|thought", "#have#": "has|have|had", "#blow#": "blow|blew", "#build#": "build|built", "#do#": "do|did|done", "#can#": "can|could", "#grow#":"grow|grew|grown", "#hang#": "hang|hung", "#run#": "run|ran", "#stand#": "stand|stood", "#string#": "string|strung", "#hold#" : "hold|held", "#take#" : "take|took|taken"}
elif language == "Spanish":
    not_wanted_adj = ["otro","mio","tuyo","suyo","nuestro","vuestro","mismo","primero","segundo","último"]
    additional = []
    for adj in not_wanted_adj:
       additional += [adj[:-1] + "a", adj[:-2] + "os", adj[:-2] + "as"]
    not_wanted_adj += additional
    not_wanted_adv = ["básicamente", "claramente","ampliamente", "atentamente", "completamente"]
    not_wanted_verb = ["haber", "estar"]
    negators = ["no", "ni", "nunca", "jamás", "nada", "nadie", "ninguno", "ningunos", "ninguna", "ningunas", "faltar", "falta", "sin"]
    punct = [".", ",", ";", "!", "?", ":", ")", "(", "\"", "'", "-", "¡", "¿"]
    sent_punct = [".", ";", "!", "?", ":", "\n", "\r", "¡", "¿"]
    skipped = {"AQ": [ "a", "estar", "haber", "hacer", "de", "como", "NC", "PP", "DP", "DD", "DI", "DA", "RG"], "RG": ["VM", "VA", "VS"], "VM":["haber", "estar", "PP"], "NC":["DP", "DD", "DI", "DA", "AQ", "AO", "de", "tener", "hacer", "estar", "con", "incluso"]}
    comparatives = ["más", "menos", "como"]
    definites = ["el", "la", "los", "las", "este", "esta", "estos", "estas", "de", "DP"]
    accents = {"í": "i", "ó": "o", "ú": "u", "é": "e", "á": "a", "ñ": "n"}
    noun_tag = "NC"
    verb_tag = "VM"
    adj_tag = "AQ"
    adv_tag = "RG"
    macro_replace = {"#NP?#": "[DI|DP|DA]?_[AQ|AC]?_[NC|NP]?_[AQ]?"}

weight_tags = config["weight_tags"]
weights_by_location = config["weights_by_location"]
highlighters = config["highlighters"]
irrealis = config["irrealis"]
boundary_words = config["boundary_words"]

def same_lists(list1, list2):
    return list1 == list2

def get_multiword_entries(string):
    if "#" in string:  #如果有宏替换
        for item in macro_replace:
            string = string.replace(item, macro_replace[item])
    words = string.split("_")
    entry = []
    keyindex = len(words) - 1 # 默认使用最后一个词
    for index in range(len(words)):
        word = words[index]
        slot = []
        if word[0] == "(":
            slot.append(1)
            slot.append(word[1:-1].split("|"))
            keyindex = index # 找到键索引
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
        final_entries = [[key, entry]]
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

def load_dictionary(filepointer, s_dict, c_dict):
    for line in filepointer.readlines():
        pair = line.strip().split()
        if len(pair) == 2:
            if "_" not in pair[0]:  #如果是单词
                if language == "Spanish" and has_accent(pair[0]):
                    s_dict[remove_accents(pair[0])] = float(pair[1])
                s_dict[pair[0]] = float(pair[1]) #放入简单词典
            elif use_multiword_dictionaries:
                entries = get_multiword_entries(pair[0])
                for entry in entries:
                    if entry[0] not in c_dict:
                        c_dict[entry[0]] = [[entry[1], float(pair[1])]]
                    else:
                        c_dict[entry[0]].append([entry[1], float(pair[1])])
    filepointer.close()

def load_extra_dict(filepointer):
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
                if "_" not in pair[0]:  #如果是单词
                    s_dict[pair[0]] = float(pair[1]) #放入简单词典
                elif use_multiword_dictionaries:
                    entries = get_multiword_entries(pair[0])
                    for entry in entries:
                        if entry[0] not in c_dict:
                            c_dict[entry[0]] = [[entry[1], float(pair[1])]]
                        else:
                            for old_entry in c_dict[entry[0]]: # 去重
                                if same_lists(old_entry[0], entry[1]):
                                    c_dict[entry[0]].remove(old_entry)
                            c_dict[entry[0]].append([entry[1], float(pair[1])])
    filepointer.close()

def load_dictionaries():
    for filename in os.listdir(args.dic_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(args.dic_folder, filename)
            with open(filepath, encoding="ISO-8859-1") as filepointer:
                if "adj" in filename:
                    load_dictionary(filepointer, adj_dict, c_adj_dict)
                elif "adv" in filename:
                    load_dictionary(filepointer, adv_dict, c_adv_dict)
                elif "verb" in filename:
                    load_dictionary(filepointer, verb_dict, c_verb_dict)
                elif "noun" in filename:
                    load_dictionary(filepointer, noun_dict, c_noun_dict)
                elif "int" in filename:
                    load_dictionary(filepointer, int_dict, c_int_dict)
    if extra_dict_path:
        load_extra_dict(open(extra_dict_path, encoding="ISO-8859-1"))
    if simple_SO:
        for s_dict in [adj_dict, adv_dict, verb_dict, noun_dict]:
            for entry in s_dict:
                if s_dict[entry] > 0:
                    s_dict[entry] = 2
                elif s_dict[entry] < 0:
                    s_dict[entry] = -2
        for entry in int_dict:
            if int_dict[entry] > 0:
                int_dict[entry] = 0.5
            elif int_dict[entry] < 0 and int_dict[entry] > -1:
                int_dict[entry] = -0.5
            elif int_dict[entry] < -1:
                int_dict[entry] = -2
        for c_dict in [c_adj_dict, c_adv_dict, c_verb_dict, c_noun_dict]:
            for entry in c_dict:
                for i in range(len(c_dict[entry])):
                    if c_dict[entry][i][1] > 0:
                        c_dict[entry][i] = [c_dict[entry][i][0], 2]
                    elif c_dict[entry][i][1] < 0:
                        c_dict[entry][i] = [c_dict[entry][i][0], -2]
        for entry in c_int_dict:
            for i in range(len(c_int_dict[entry])):
                if c_int_dict[entry][i][1] > 0:
                    c_int_dict[entry][i] = [c_int_dict[entry][i][0], 0.5]
                elif c_int_dict[entry][i][1] < 0 and c_int_dict[entry][i][1] > -1:
                    c_int_dict[entry][i] = [c_int_dict[entry][i][0], -0.5]
                elif c_int_dict[entry][i][1] < -1:
                    c_int_dict[entry][i] = [c_int_dict[entry][i][0], -2]

def convert_fraction(fraction):
    if "/" not in fraction:
        return float(fraction)
    else:
        fraction = fraction.split("/")
        if len(fraction) == 2:
            return float(fraction[0]) / float(fraction[1])
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
                new_ranges.append([start, end, weights_by_location[range]])
    return new_ranges

def fill_text_and_weights(infile):
    global text, weights, boundaries
    text = []
    weights = []
    boundaries = []
    weight = 1.0 # 起始权重为1
    temp_weight = 1.0 # 跟踪零权重前的权重
    for line in infile.readlines():
        line = line.replace("<", " <").replace(">", "> ")
        for word in line.strip().split(" "):
            if word:
                if word[0] == "<" and word[-1] == ">": #XML标签
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
                                weight /= weight_modifier # 移除权重
                            else:
                                weight = temp_weight # 使用零权重前的权重
                        else:
                            if weight_modifier != 0:
                                weight *= weight_modifier # 增加权重
                            else:
                                temp_weight = weight # 保存当前权重
                                weight = 0
                elif "/" in word:
                    text.append(word.split("/"))
                    weights.append(weight)
        boundaries.append(len(text))
    if use_weight_by_location:  # 添加位置权重
        range_dict = convert_ranges()
        for i in range(len(weights)):
            for interval in range_dict:  #如果当前索引在范围内
                if interval[0] <= float(i)/len(weights) and interval[1] > float(i)/len(weights):
                    weights[i] *= interval[2]  #增加权重
    infile.close()

def stem_NN(NN):
    if NN not in noun_dict and NN not in c_noun_dict and  len(NN) > 2 and NN[-1] == "s":   # boys -> boy
        NN = NN[:-1]
        if NN not in noun_dict and NN not in c_noun_dict and NN[-1] == "e": # watches -> watch
            NN = NN[:-1]
            if NN not in noun_dict and NN not in c_noun_dict and NN[-1] == "i": # flies -> fly
                NN = NN[:-1] + "y"
    return NN

def stem_VB(VB, type):
    if type == "" or type == "P" or len(VB) < 4 or VB in verb_dict or VB in c_verb_dict:
        return VB
    elif type == "D" or type == "N":
        if VB[-1] == "d":
            VB = VB[:-1]   #  loved -> love
            if not VB in verb_dict and not VB in c_verb_dict:
                if VB[-1] == "e":
                    VB = VB[:-1]   # enjoyed -> enjoy
                if not VB in verb_dict and not VB in c_verb_dict:
                    if VB[-1] == "i":
                        VB = VB[:-1] + "y" # tried -> try
                    elif len(VB) > 1 and VB[-1] == VB[-2]:
                        VB = VB[:-1]   # compelled -> compel
        return VB
    elif type == "G":
        VB = VB[:-3] # obeying -> obey
        if not VB in verb_dict and not VB in c_verb_dict:
            if len(VB) > 1 and VB[-1] == VB[-2]:
                VB = VB[:-1] # stopping -> stop
            else:
                VB = VB + "e" # amusing -> amuse
        return VB
    elif type == "Z" and len(VB) > 3:
        if VB[-1] == "s":
            VB = VB[:-1]  # likes -> like
            if VB not in verb_dict and not VB in c_verb_dict and VB[-1] == "e":
                VB = VB[:-1]  # watches -> watch
                if VB not in verb_dict and not VB in c_verb_dict and VB[-1] == "i":
                    VB = VB[:-1] + "y"  # flies -> fly
        return VB

def stem_RB_to_JJ(RB):
    JJ = RB
    if len(JJ) > 3 and JJ[-2:] == "ly":
        JJ = JJ[:-2]  # sharply -> sharp
        if not JJ in adj_dict:
            if JJ + "l" in adj_dict:
                JJ += "l" # full -> fully
            elif JJ + "le" in adj_dict:
                JJ += "le" # simply -> simple
            elif JJ[-1] == "i" and JJ[:-1] + "y" in adj_dict:
                JJ = JJ[:-1] + "y" # merrily -> merry
            elif len(JJ) > 5 and JJ[-2:] == "al" and JJ[:-2] in adj_dict:
                JJ = JJ[:-2] # angelic -> angelically
    return JJ

def stem_ative_adj(JJ):
    if JJ not in adj_dict:
        if JJ + "e" in adj_dict:
            JJ += "e" # abler/ablest -> able
        elif JJ[:-1] in adj_dict:
            JJ = JJ[:-1] # bigger/biggest -> big
        elif JJ[-1] == "i" and JJ[:-1] + "y" in adj_dict:
            JJ = JJ[:-1] + "y" # easier/easiest -> easy
    return JJ

def stem_comp_JJ(JJ):
    if JJ[-2:] == "er":
        JJ = stem_ative_adj(JJ[:-2]) # fairer -> fair
    return JJ

def stem_super_JJ(JJ):
    if JJ[-3:] == "est":
        JJ = stem_ative_adj(JJ[:-3]) # fairest -> fair
    return JJ

def stem_NC(NC):
    if NC not in noun_dict and len(NC) > 2 and NC[-1] == "s":   # diplomas -> diploma
        NC = NC[:-1]
    if NC not in noun_dict and NC not in c_noun_dict and len(NC) > 1:
        if NC[-1] == "a":
            NC = NC[:-1] + "o" #hermanas -> hermano
        elif NC[-1] == "e": # actor -> actores
            NC = NC[:-1]
    return NC

def stem_AQ(AQ):
    if AQ not in adj_dict and len(AQ) > 2 and AQ[-1] == "s":   # buenos -> bueno
        AQ = AQ[:-1]
    if AQ not in adj_dict and AQ not in c_adj_dict and len(AQ) > 1:
        if AQ[-1] == "a":    # buena -> bueno
            AQ = AQ[:-1] +  "o"
        elif AQ[-1] == "e": #  -> watch
            AQ = AQ[:-1]
    return AQ

def stem_RG_to_AQ(RG):
    AQ = RG
    if len(AQ) > 6 and AQ[-5:] == "mente" :
        AQ = AQ[:-5]  # felizmente -> feliz
        if not AQ in adj_dict:
            if AQ[-1] == "a":
                AQ = AQ[:-1] + "o" # nuevamente -> nuevo
    return AQ

def stem_super_AQ(AQ):
    if AQ not in adj_dict:
        if len(AQ) > 6 and AQ[-5:] in ["ísima", "ísimo", "isima", "isimo"]:
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

def get_word(pair): return pair[0] # 获取单词对中的单词
def get_tag(pair): return pair[1] # 获取单词对中的标签

def sum_word_counts(word_count_dict):
    count = 0
    for word in word_count_dict:
        count += word_count_dict[word]
    return count

def find_intensifier(index):
    if index < 0 or index >= len(text) or get_tag(text[index]) == "MOD": # 已经修改了某些东西
        return False
    if get_word(text[index]).lower() in c_int_dict: # 可能是复杂的
        for word_mod_pair in c_int_dict[get_word(text[index]).lower()]:
            if same_lists(word_mod_pair[0][:-1], map(str.lower, map(get_word, text[index - len(word_mod_pair[0]) + 1:index]))):
                return [len(word_mod_pair[0]), word_mod_pair[1]]
    if get_word(text[index]).lower() in int_dict: # 简单的强化词
        modifier = int_dict[get_word(text[index]).lower()]
        if get_word(text[index]).isupper() and use_cap_int: # 如果大写
             modifier *= capital_modifier   # 增加修饰
        return [1, modifier]
    return False

def match_multiword_f(index, words):
    if len(words) == 0:
        return [0, 0] #完成
    else:
        current = words[0]
        if not isinstance(current, list):
            current = [1, [current]] # 未修饰的词应出现一次
        if current[0] == "0":
            return match_multiword_f(index, words[1:]) #这个词完成
        if current[0] == "*" or current[0] == "?": # 词可选 - 尝试
            temp = match_multiword_f(index, words[1:]) # 无首词
            if temp[0] != -1:
                return temp
        if index == len(text):
            return [-1, 0] # 达到文本末尾
        match = False
        for word_or_tag in current[1]:
            if word_or_tag.islower(): #匹配单词
                match = match or get_word(text[index]).lower() == word_or_tag
            elif word_or_tag.isupper(): #匹配标签
                if word_or_tag == "INT": # 如果寻找修饰词
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
                return temp #失败
            else:
                return [temp[0] + 1, temp[1]] #成功

def match_multiword_b(index, words):
    if len(words) == 0:
        return [0, 0]
    else:
        current = words[-1]
        if not isinstance(current, list):
            current = [1, [current]]
        if current[0] == "0":
            return match_multiword_b(index, words[:-1])
        if current[0] == "*" or current[0] == "?":
            temp = match_multiword_b(index, words[:-1])
            if temp[0] != -1:
                return temp
        if index == -1:
            return [-1, 0]
        match = False
        for word_or_tag in current[1]:
            if word_or_tag.islower():
                match = match or get_word(text[index]).lower() == word_or_tag
            elif word_or_tag.isupper():
                if word_or_tag == "INT":
                    intensifier = find_intensifier(index)
                    if intensifier:
                        i = intensifier[0]
                        result = match_multiword_b(index - i, words[:-1])
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
                return temp #失败
            else:
                return [temp[0] + 1, temp[1]] #成功

def match_multiword_entries(index, dictionary, forward=True):
    if forward:
        for word_mod_pair in dictionary:
            result = match_multiword_f(index, word_mod_pair[0])
            if result[0] != -1:
                return [result[0], result[1] * word_mod_pair[1]]
    else:
        for word_mod_pair in dictionary:
            result = match_multiword_b(index, word_mod_pair[0])
            if result[0] != -1:
                return [result[0], result[1] * word_mod_pair[1]]
    return [0, 0]

def find_adj(index):
    if get_tag(text[index]) == adj_tag and get_word(text[index]).lower() not in not_wanted_adj:
        if get_word(text[index]).lower() in adj_dict:
            return [1, adj_dict[get_word(text[index]).lower()]]
        if use_multiword_dictionaries and get_word(text[index]).lower() in c_adj_dict:
            return match_multiword_entries(index, c_adj_dict[get_word(text[index]).lower()])
    return [0, 0]

def find_adv(index):
    if get_tag(text[index]) == adv_tag and get_word(text[index]).lower() not in not_wanted_adv:
        if get_word(text[index]).lower() in adv_dict:
            return [1, adv_dict[get_word(text[index]).lower()]]
        if use_multiword_dictionaries and get_word(text[index]).lower() in c_adv_dict:
            return match_multiword_entries(index, c_adv_dict[get_word(text[index]).lower()])
    return [0, 0]

def find_verb(index):
    if get_tag(text[index]) == verb_tag:
        if get_word(text[index]).lower() in verb_dict:
            return [1, verb_dict[get_word(text[index]).lower()]]
        if use_multiword_dictionaries and get_word(text[index]).lower() in c_verb_dict:
            return match_multiword_entries(index, c_verb_dict[get_word(text[index]).lower()])
    return [0, 0]

def find_noun(index):
    if get_tag(text[index]) == noun_tag:
        if get_word(text[index]).lower() in noun_dict:
            return [1, noun_dict[get_word(text[index]).lower()]]
        if use_multiword_dictionaries and get_word(text[index]).lower() in c_noun_dict:
            return match_multiword_entries(index, c_noun_dict[get_word(text[index]).lower()])
    return [0, 0]

def calculate_SO(text, weights):
    text_SO = 0
    SO_counter = 0
    for index in range(len(text)):
        SO_value = 0
        if use_adjectives:
            SO_value = find_adj(index)[1] * adj_multiplier
        if use_adverbs:
            SO_value += find_adv(index)[1] * adv_multiplier
        if use_verbs:
            SO_value += find_verb(index)[1] * verb_multiplier
        if use_nouns:
            SO_value += find_noun(index)[1] * noun_multiplier
        if SO_value != 0:
            text_SO += SO_value * weights[index]
            SO_counter += 1
    return text_SO, SO_counter

def read_files():
    for filename in os.listdir(args.input):
        if filename.endswith(".txt"):
            filepath = os.path.join(args.input, filename)
            with open(filepath, encoding="ISO-8859-1") as infile:
                fill_text_and_weights(infile)
                text_SO, SO_counter = calculate_SO(text, weights)
                # 修改此行以仅写入文件名和情感分数
                basicout.write(f"{filename}\t{text_SO}\n")
    basicout.close()

load_dictionaries()
read_files()
