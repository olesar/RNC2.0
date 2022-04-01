import re
from bs4 import BeautifulSoup
from string import whitespace

less_symb_replacer = chr(17)


def get_list_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    some_list = text.split('\n')
    return some_list


def replace_xml_codes(text):
    xml_symbs = re.findall(r'(&(amp;)*#?\w+;)', text)
    if xml_symbs != []:
        for s in xml_symbs:
            sym = s[0]
            while 'amp;' in sym:
                sym = sym.replace('&amp;', '&')
            soup = BeautifulSoup(sym, 'html.parser')
            normal_s = soup.text
            if '&' in normal_s and len(normal_s) > 1:
                normal_s = ''
            if normal_s == '<':
                normal_s = less_symb_replacer
            text = text.replace(s[0], normal_s)
    return text


def get_sents(text):
    body_text = re.search('<body>(.+)</body>', text, re.DOTALL)
    text = body_text.group(1).strip()
    text = replace_xml_codes(text)
    sents = text.split('<se>')
    return sents


def split_punct_with_tags(punct_line):
    tags = []
    punct_with_tags = []
    index = 0
    while index < len(punct_line):
        leftover_s = punct_line[index:]
        char = punct_line[index]
        if char == '<':
            tag = leftover_s[:leftover_s.find('>') + 1].strip()
            tags.append(tag)
            index += leftover_s.find('>') + 1
        else:
            if char not in whitespace:
                d = {}
                d['punct'] = char
                d['tags'] = tags
                punct_with_tags.append(d)
                tags = []
            index += 1
    d = {}
    d['punct'] = None
    d['tags'] = tags
    punct_with_tags.append(d)
    return punct_with_tags


def divide_between_sents(punct_tag_line):
    break_punct = '.,!?)]}:;'
    to_prev_sent, in_this_sent = '', ''
    current_to_prev = ''
    was_tag = False
    for p in punct_tag_line:
        if p['punct'] is None:
            p['punct'] = ''
        if len(p['tags']) != 0:
            was_tag = True
        if was_tag:
            in_this_sent += ''.join(p['tags']) + p['punct']
            continue
        current_to_prev += p['punct']
        if p['punct'] != '' and p['punct'] in break_punct:
            to_prev_sent += current_to_prev
            current_to_prev = ''
    in_this_sent = current_to_prev + in_this_sent
    return to_prev_sent, in_this_sent


def fix_punctuation(text):
    sents = get_sents(text)
    for i in range(2, len(sents)):
        sent = sents[i]
        before_word = sent.split('<w>')[0]
        punct_tag_line = split_punct_with_tags(before_word)
        prev, curr = divide_between_sents(punct_tag_line)
        sents[i] = curr + '\n' + '<w>' + '<w>'.join(sent.split('<w>')[1:])
        prev_parts = sents[i - 1].split('</se>')
        if prev == '.':
            prev = '..'
        sents[i - 1] = prev_parts[0] + prev + '</se>' + prev_parts[1]
    new_text = '<se>'.join(sents)
    new_text = new_text.replace(less_symb_replacer, '<')
    return '<body>\n' + new_text + '\n</body>'


# with open('test_files_RNC\\marx.xml', 'r', encoding='utf-8') as f:
#     text = f.read()
# new_text = fix_punctuation(text)
# with open('test_files_RNC\\marx-fixed.xml', 'w', encoding='utf-8') as f:
#     f.write('<body>\n' + new_text + '\n</body>')
