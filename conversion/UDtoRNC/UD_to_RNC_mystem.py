import re
import RNC_to_UD_add_ext_synt
import os
from tqdm import tqdm
import multiprocessing as mp
import traceback
import html
from copy import deepcopy
from hyphen_test import add_we_to_disjointed
import mystem_ext
import argparse


# считывание файла для перевода тегов UD в RNC формат
def get_RNCtoUD_table(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tags_table = f.read()
    tags = tags_table.split('\n')
    tags_dict = {}
    for tag in tags:
        if tag != '':
            parts = tag.split('\t')
            tags_dict[parts[1]] = parts[0]
    return tags_dict


# считывание файла с видовыми парами глаголов
def get_verb_table(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        verb_table = f.read()
    lines = verb_table.split('\n')[:-1]
    ipf_dict = {}
    pf_dict = {}
    for line in lines:
        parts = line.split(' ')
        ipf_dict[parts[0]] = parts[1]
        pf_dict[parts[1]] = parts[0]
    return ipf_dict, pf_dict


tags_dict = get_RNCtoUD_table('data_lists/RNCtoUDtable-ext.txt')
verb_ipf_dict, verb_pf_dict = get_verb_table('data_lists/aspect_pair_candidates_2.vocab')
with open('data_lists/half.txt', 'r', encoding='utf-8') as f:
    text = f.read()
half_list = text.split('\n')[:-1]



def get_rnc_pos(ud_pos, ud_gram, tags_dict, lex):
    rnc_pos = tags_dict[ud_pos]
    praedicpro_lemmas = ['некого', 'нечего', 'незачем', 'негде', 'некуда', 'неоткуда']
    if ud_pos == 'PROPN' and 'Abbr=Yes' not in ud_gram:
        rnc_pos = 'S'
    elif lex == 'один' and ud_pos == 'NUM':
        rnc_pos = tags_dict['ANUM']
    elif lex == 'который':
        rnc_pos = 'APRO'
    elif lex == 'нет':
        rnc_pos = 'PRAEDIC'
    elif lex in praedicpro_lemmas:
        rnc_pos = 'PRAEDICPRO'
    return rnc_pos


def get_rnc_gram(ud_gram, tags_dict):
    grams = ud_gram.split('|')
    if 'Number=Count' in ud_gram:
        grams.append('Number=Sing')
    rnc_grams = []
    for gram in grams:
        if gram not in tags_dict.keys():
            continue
        rnc_gram = tags_dict[gram]
        if rnc_gram != '':
            rnc_grams.append(tags_dict[gram])
    rnc_grams_sorted = sorted(rnc_grams)
    return '.'.join(rnc_grams_sorted)


def get_rnc_tags(ud_lex, ud_pos, ud_gram):
    rnc_pos = get_rnc_pos(ud_pos, ud_gram, tags_dict, ud_lex)
    if ud_gram == '_' and (ud_pos == 'PUNCT' or ud_pos == 'SYM'):
        rnc_tags = ud_pos + '.'
    elif ud_gram == '_':
        rnc_tags = ud_lex + ':' + rnc_pos + '.'
    else:
        rnc_gram = get_rnc_gram(ud_gram, tags_dict)
        if rnc_gram == '':
            rnc_tags = ud_lex + ':' + rnc_pos + '.'
        else:
            rnc_tags = ud_lex + ':' + rnc_pos + '.' + rnc_gram + '.'
    return rnc_tags


def escape_tag_params(tags):
    infos = re.findall('"(.*?)"', tags)
    infos_escaped = [html.escape(inf) for inf in infos]
    for i in range(len(infos)):
        tags = tags.replace(infos[i], infos_escaped[i])
    return tags


def collect_misc_info(line):
    parts = line.split('\t')
    misc = parts[9].split('|')
    spaces = '\n'
    close_tags = ''
    open_tags = ''
    word_form = ''
    tag_part = ''
    hyph_tag = ''
    at_pos = {}
    for i in range(len(misc)):
        if misc[i].startswith('before='):
            if misc[i].endswith('>'):
                open_tags = misc[i].replace('before=', '')
                open_tags = escape_tag_params(open_tags)
            else:
                tag_part = misc[i]
                continue
        elif misc[i].startswith('after='):
            close_tags = misc[i].replace('after=', '')
            close_tags = escape_tag_params(close_tags)
        elif 'SpacesAfter=' in misc[i] or 'SpaceAfter=' in misc[i]:
            spaces = misc[i].replace('SpacesAfter=', '').replace('SpaceAfter=', '')
            spaces = spaces.replace('\\n', '\n').replace('\\t', '\t').replace('\\s', ' ')
            if spaces == 'No':
                spaces = ''
        elif misc[i].startswith('wf='):
            word_form = misc[i].replace('wf="', '')[:-1]
            word_form = html.escape(word_form)
        elif misc[i].startswith('at_pos'):
            at_pos[int(misc[i].split(':', 1)[1].split('=', 1)[0])] = misc[i].split('=', 1)[1]
        elif misc[i].startswith('WI') or misc[i].startswith('WE'):
            hyph_tag = misc[i]
        elif misc[i].endswith('>'):  # if | was in tag parameters!
            misc[i] = tag_part + '|' + misc[i]
            open_tags = misc[i].replace('before=', '')
    if '\n\n' in spaces and ('</p>' in close_tags or '</speech>' in close_tags):
        spaces = spaces.replace('\n\n', '', 1)
    return open_tags, close_tags, spaces, word_form, at_pos, hyph_tag


def delete_body_tag(sent, closing):
    tag = '<body>'
    addition = 'before='
    if closing:
        tag = '</body>'
        addition = 'after='
    lines = sent.split('\n')
    for j, line in enumerate(lines):
        if line[0] == '#':
            continue
        parts = line.split('\t')
        misc = parts[9].split('|')
        for i in range(len(misc)):
            if misc[i] == addition + tag:
                misc[i] = '_'
            elif misc[i].startswith(addition):
                misc[i] = misc[i].replace(tag, '')
        parts[9] = '|'.join(misc)
        lines[j] = '\t'.join(parts)
    return '\n'.join(lines)


def make_rnc_gram_lemmas(gr, lex):
    grams = []
    lemmas = []
    parts = gr.split('|')
    for p in parts:
        if ':' not in p:
            lemmas.append(lex)
        else:
            lemmas.append(':'.join(p.split(':')[:-1]))
            p = p.split(':')[-1]
        grams.append(p.replace('.', ',')[:-1])
    return grams, lemmas


def get_word_info(line):
    info_dict = {}
    parts = line.split('\t')
    info_dict['token'] = html.escape(parts[1])
    info_dict['pos'] = html.escape(parts[3])
    info_dict['gr'], info_dict['lex'] = make_rnc_gram_lemmas(parts[4], parts[2])
    info_dict['lex'] = [html.escape(lex) for lex in info_dict['lex']]
    if parts[8] != '_':
        info_dict['synt'] = html.escape(parts[7]) + ',' + html.escape(parts[8].replace('|', ','))
    else:
        info_dict['synt'] = html.escape(parts[7])
    return info_dict


def check_sent_tag(tags, tag_type): #tag_type = 'speech' or '/speech'
    sent_tag = ''
    full_tag = re.search('<{}(\s.+?)?>'.format(tag_type), tags)
    if full_tag:
        full_tag = full_tag.group()
        tags = tags.replace(full_tag, '')
        sent_tag = full_tag
    return sent_tag, tags


def separate_tags(tag_seq):
    tags = tag_seq.split('>')[:-1]
    tags = [tag + '>' for tag in tags]
    return tags


# четыре функции для сохранения валидного xml с тегами
def add_to_stack(before_tags, inside_tags, after_tags, some_stack):
    tags = separate_tags(before_tags + ''.join(inside_tags) + after_tags)
    for tag in tags:
        if tag.startswith('</'):
            tag_name = some_stack[-1].split()[0][1:]
            if tag_name[-1] == '>':
                tag_name = tag_name[:-1]
            close_pair = '</{}>'.format(tag_name)
            if close_pair != tag:
                print("ERROR IN TAGS! Closing tag {} doesn't match opening {}".format(tag, tag_name))
            some_stack.pop()
        else:
            some_stack.append(tag)
    return some_stack


def collect_all_opening(some_stack):
    return ''.join(some_stack)


def collect_all_closing(some_stack):
    close_all = ''
    for tag in some_stack[::-1]:
        tag_name = tag.split()[0][1:]
        if tag_name[-1] == '>':
            tag_name = tag_name[:-1]
        close_pair = '</{}>'.format(tag_name)
        close_all += close_pair
    return close_all


def count_balance(lines):
    balance = 0
    min_balance = 0
    for line in lines:
        open_tags, close_tags, space_after, word_form, at_pos, hyph_tag = collect_misc_info(line)
        tags = separate_tags(open_tags) + \
               separate_tags(''.join(at_pos.values())) +\
               separate_tags(close_tags)
        for tag in tags:
            if tag.startswith('</'):
                balance -= 1
            else:
                balance += 1
            min_balance = min(balance, min_balance)
    return min_balance


def add_joined_hyphen(s):
    index = 0
    while True:
        whole = ''
        match = re.search('</w>[-‑–—-]+<w', s[index:])
        if not match:
            break
        span = match.span()
        span = (span[0] + index, span[1] + index)
        part = s[:span[0]]
        posit = part.rfind('<w')
        change_part = part[posit:]
        anas = re.findall('<ana.*?>', change_part)
        for ana in anas:
            if 'joined=' not in ana:
                new_ana = ana[:-1] + ' joined="hyphen">'
                change_part = change_part.replace(ana, new_ana)
        full_line = part[:posit] + change_part
        whole += full_line + match.group()
        index = len(whole) + 1

        part = s[span[1]:]
        posit = part.find('</w>')
        change_part = part[:posit]
        anas = re.findall('<ana .*?>', change_part)
        for ana in anas:
            if 'joined=' not in ana:
                new_ana = ana[:-1] + ' joined="hyphen">'
                change_part = change_part.replace(ana, new_ana)
        full_line = change_part + part[posit:]
        whole += full_line
        s = whole
    return s

# две функции для создания external и internal вариантов дефисных слов
def get_wi_subline(info):
    subtokens = re.split('[-—‑–]+', info['token'])
    sublemmas = re.split('[-—‑–]+', info['lex'][0])
    sub_f = '<wi><ana lex="{}" itoken="{}"/></wi>'
    subs = []
    for sub_i in range(len(sublemmas)):
        s = sub_f.format(sublemmas[sub_i], subtokens[sub_i])
        subs.append(s)
    sub_line = '-'.join(subs)
    return sub_line


def find_we_end(lines, i_after):
    for i in range(i_after + 1, len(lines)):
        line = lines[i]
        open_tags, close_tags, space_after, word_form, at_pos, hyph_tag = collect_misc_info(line)
        if 'WE-END' in hyph_tag:
            return i
    raise "No WE-END after WE-START"


def separate_closing_and_opening(tag_list):
    opening = []
    closing = []
    for tag_line in tag_list:
        tags = separate_tags(tag_line)
        for tag in tags:
            if tag.startswith('</'):
                closing.append(tag)
            else:
                opening.append(tag)
    return closing, opening


# три функции для сохранения валидного xml при вынесении всех тегов за <w> тег
def collect_inside_tags_right_seq(all_tags):
    closing_who_opened_BEFORE = []
    stack = []
    for t in all_tags:
        if t[:2] != '</':
            tag_name = t.split()[0][1:]
            if tag_name[-1] == '>':
                tag_name = tag_name[:-1]
            tag_clean = f"<{tag_name}>"
            stack.append(tag_clean)
        elif len(stack) > 0 and t == '</' + stack[-1][1:]:
            stack.pop()
        else:
            closing_who_opened_BEFORE.append(t)
    opening_who_closed_AFTER = stack
    return opening_who_closed_AFTER, closing_who_opened_BEFORE


def construct_new_open_and_close(opening_pos, closing_who_opened_BEFORE, opening_who_closed_AFTER):
    closing_first = []
    for t in opening_pos[::-1]:
        tag_name = t.split()[0][1:]
        if tag_name[-1] == '>':
            tag_name = tag_name[:-1]
        tag_close = f"</{tag_name}>"
        closing_first.append(tag_close)
    closing_second = closing_who_opened_BEFORE
    opening_again = opening_who_closed_AFTER
    return ''.join(opening_pos), ''.join(closing_first) + ''.join(closing_second) + ''.join(opening_again)


def reformat_tag_lines(open_tags, close_tags, at_pos):
    closing_pos, opening_pos = separate_closing_and_opening(at_pos.values())
    open_list = separate_tags(open_tags)
    close_list = separate_tags(close_tags)
    all_tags = deepcopy(open_list)
    for t in at_pos.values():
        all_tags.extend(separate_tags(t))
    all_tags.extend(close_list)
    open_c, open_o = separate_closing_and_opening(open_list)
    close_c, close_o = separate_closing_and_opening(close_list)
    open_o.extend(opening_pos)
    open_o.extend(close_o)
    opening_pos = open_o
    opening_who_closed_AFTER, closing_who_opened_BEFORE = collect_inside_tags_right_seq(all_tags)
    open_new, close_new = construct_new_open_and_close(opening_pos,
                                                       closing_who_opened_BEFORE, opening_who_closed_AFTER)
    return open_new, close_new


def half_pol_condition(pos, lex):  # ПОЛ
    if pos in ['NOUN', 'PROPN', 'ADJ', 'ANUM']:
        if lex[:4] not in ['поли', 'полу']:
            if not lex.startswith('полно') or lex in ['полноги', 'полночи', 'полнормы']:
                if re.match('пол.*([аяыи]|(го)|(ой)|(ых))', lex) \
                        and re.match('пол.*([аяыи]|(го)|(ой)|(ых))', lex).group() == lex:
                    if lex not in half_list:
                        return True
    return False


def half_polu_condition(pos, lex, gram):  # ПОЛУ
    if pos in ['VERB', 'AUX']:
        if lex not in half_list:
            if 'ger' in gram or 'partcp' in gram:
                if lex.startswith('полу'):
                    return True
    return False


def half_neg_condition(pos, lex, gram): # НЕ
    if pos in ['VERB', 'AUX']:
        if 'ger' in gram or 'partcp' in gram:
            if lex.startswith('не') and not lex.startswith('недо'):
                return True
    return False



def transform_sent(sent, some_stack):
    new_lines = []
    f_ana = '<ana lex="{}" gr="{}"{}{}></ana>' # '' in the last if no word_form
    lines = sent.split('\n')
    tags_to_open = ''
    we_started = False
    opened_inside_we = None
    close_before_we = None
    open_after_we = None
    we_dict = {'tokens': [], 'lemmas': []}
    for tag in some_stack:
        tags_to_open += tag
    for i, line in enumerate(lines):
        info = get_word_info(line)
        mext = mystem_ext.extend_by_mystem(info)
        open_tags, close_tags, space_after, word_form, at_pos, hyph_tag = collect_misc_info(line)
        open_new, close_new = reformat_tag_lines(open_tags, close_tags, at_pos)
        # добавление пунктуации без <w>
        if info['pos'] == 'SYM' or info['pos'] == 'PUNCT':
            new_line = html.escape(info['lex'][0])
            if i > 0:
                new_lines[i-1] = new_lines[i-1].strip()
            elif i == 0:
                new_line = new_line.strip()
            some_stack = add_to_stack(open_tags, at_pos.values(), close_tags, some_stack)
            if i != 0:
                tags_to_open = ''
            # at_pos = {'': ''}
            open_tags = open_new
            close_tags = close_new
            new_lines.append(tags_to_open + open_tags + new_line + close_tags + space_after)
        else:
            ana_lines = []
            for j, gr in enumerate(info['gr']):
                # добавление дополнительной видовой формы глагола
                ipf_pf_form = ''
                if info['pos'] == 'VERB' and info['lex'][j].lower() in verb_ipf_dict:
                    ipf_pf_form = ' lex_ipf="{}"'.format(verb_ipf_dict[info['lex'][j].lower()])
                elif info['pos'] == 'VERB' and info['lex'][j].lower() in verb_pf_dict:
                    ipf_pf_form = ' lex_pf="{}"'.format(verb_pf_dict[info['lex'][j].lower()])

                # NEW HALF RULES
                if half_pol_condition(info['pos'], info['lex'][j]):
                    extra_ana = '<ana lex="пол" gr="COM"></ana>'
                    ana_lines.append(extra_ana)
                elif half_polu_condition(info['pos'], info['lex'][j], gr):
                    extra_ana = '<ana lex="полу" gr="COM"></ana>'
                    ana_lines.append(extra_ana)
                elif info['lex'][j].count('+') == 1:
                    lex_splits = info['lex'][j].split('+')
                    extra_ana = f'<ana lex="{lex_splits[0]}"></ana>'
                    ana_lines.append(extra_ana)
                    info['lex'][j] = lex_splits[1]
                elif half_neg_condition(info['pos'], info['lex'][j], gr):
                    extra_ana = '<ana lex="не" gr="PART"></ana>'
                    ana_lines.append(extra_ana)
                    cut_lex = info['lex'][j][2:]
                    if cut_lex[0] in ['-', '+']:
                        cut_lex = cut_lex[1:]
                    extra_ana = f_ana.format(cut_lex, gr, '', ipf_pf_form)
                    ana_lines.append(extra_ana)

                if word_form:
                    ana = f_ana.format(info['lex'][j], gr, ' wf="{}"'.format(word_form), ipf_pf_form)
                else:
                    ana = f_ana.format(info['lex'][j], gr, '', ipf_pf_form)
                ana_lines.append(ana.replace('  ', ' '))
            whole_ana = ''.join(ana_lines)
            whole_ana += mext

            if 'WE-START' in hyph_tag:
                we_end_ind = find_we_end(lines, i)
                closed_inside_we = count_balance(lines[i:we_end_ind + 1])
                closed_inside_we += len(some_stack)
                close_before_we = collect_all_closing(some_stack[closed_inside_we:])
                open_after_we = collect_all_opening(some_stack[closed_inside_we:])
                opened_inside_we = closed_inside_we
            some_stack = add_to_stack(open_tags, list(), '', some_stack)
            open_tags = open_new
            balance = 0
            min_balance = 0  # кол-во тегов, которые закрылись и не открывались внутри <w>
            at_pos_tags = separate_tags(''.join(at_pos.values()))
            for tag in at_pos_tags:
                if tag.startswith('</'):
                    balance -= 1
                else:
                    balance += 1
                min_balance = min(balance, min_balance)
            min_balance += len(some_stack)
            some_stack = add_to_stack('', at_pos.values(), '', some_stack)
            # at_pos = {'': ''}
            some_stack = add_to_stack('', list(), close_tags, some_stack)
            close_tags = close_new

            sub_line = ''
            if 'WI' in hyph_tag:
                sub_line = get_wi_subline(info)

            word_line = f'<w flags="{info["synt"]}">{whole_ana}{sub_line}{info["token"]}</w>'

            sub_line_we = ''
            if we_started:
                we_dict['tokens'].append(info['token'])
                we_dict['lemmas'].append(info['lex'][0])
            if 'WE-START' in hyph_tag:
                we_started = True
                we_dict['tokens'] = [info['token']]
                we_dict['lemmas'] = [info['lex'][0]]
                word_line = close_before_we + '<we>' + open_after_we + open_tags + word_line
                open_tags = ''

            elif 'WE-END' in hyph_tag:
                closing_before_we_end = collect_all_closing(some_stack[opened_inside_we:])
                opening_after_we_end = collect_all_opening(some_stack[opened_inside_we:])
                sub_f = '\n<ana lex="{}" etoken="{}"></ana>{}{}</we>{}'
                sub_token = '-'.join(we_dict['tokens'])
                sub_lemma = '-'.join(we_dict['lemmas'])
                sub_line_we = sub_f.format(sub_lemma, sub_token,
                                           close_tags,
                                           closing_before_we_end,
                                           opening_after_we_end)
                close_tags = ''
                word_line = word_line + sub_line_we
                we_started = False

            if i != 0:
                tags_to_open = ''
            new_line = tags_to_open + open_tags + word_line + close_tags + space_after
            new_lines.append(new_line)
    for tag in some_stack[::-1]:
        tag_name = tag.split()[0][1:]
        if tag_name[-1] == '>':
            tag_name = tag_name[:-1]
        close_pair = '</{}>'.format(tag_name)
        new_lines[-1] = new_lines[-1] + close_pair
    new_lines_joined = ''.join(new_lines)
    new_lines = new_lines_joined.split('\n')
    for i, line in enumerate(new_lines):
        if re.search('</w>[-‑–—-]+<w', line):
           new_lines[i] = add_joined_hyphen(line)
    new_lines_joined = '\n'.join(new_lines)
    new_sent = '<se>\n' + new_lines_joined + '</se>' + '\n\n'
    return new_sent, some_stack


def is_init_normal(parts, next_parts, next_parts2):
    match = re.search('[А-Я][а-я]{0,3}', parts[1])
    if match and match.group() != parts[1]:
        return False
    if parts[5] == '_' or parts[3] != 'PROPN':
        return False
    if next_parts[1] != '.':
        return False
    if next_parts2[7] != 'flat:name':
        return False
    return True


def is_init_last(parts, prev_parts, prev_parts2):
    match = re.search('[А-Я][а-я]{0,3}', parts[1])
    if match and match.group() != parts[1]:
        return False
    if parts[5] == '_' or parts[3] != 'PROPN':
        return False
    if prev_parts[1] != '.':
        return False
    if prev_parts2[3] != 'PROPN':
        return False
    return True


def delete_meta_lines(sent):
    lines = sent.split('\n')
    meta_lines = []
    normal_lines = []
    for line in lines:
        if line[0] == '#':
            meta_lines.append(line)
        else:
            normal_lines.append(line)
    return '\n'.join(normal_lines), '\n'.join(meta_lines)


def fix_init(sent):
    sent, meta_part = delete_meta_lines(sent)
    lines = sent.split('\n')
    for i in range(len(lines)):
        if i < len(lines) - 3 and len(lines) > 2:
            parts = lines[i].split('\t')
            next_parts = lines[i+1].split('\t')
            next_parts2 = lines[i+2].split('\t')
            if is_init_normal(parts, next_parts, next_parts2):
                parts[5] += '|Abbr=Yes'
                lines[i] = '\t'.join(parts)
        elif i > 2:
            parts = lines[i].split('\t')
            prev_parts = lines[i-1].split('\t')
            prev_parts2 = lines[i-2].split('\t')
            if is_init_last(parts, prev_parts, prev_parts2):
                parts[5] += '|Abbr=Yes'
                lines[i] = '\t'.join(parts)
    fixed_sent = '\n'.join(lines)
    return meta_part + '\n' + fixed_sent


def get_sents(text):
    sents = text.split('\n\n')[:-1]
    if sents[-1].strip() == '':
        sents = sents[:-1]
    else:
        sents[-1] = sents[-1].strip()
    return sents


def add_rnc_and_fix(text):
    sents = get_sents(text)
    sents_with_rnc = []
    for sent in sents:
        sent = fix_init(sent)
        sent = sent.strip()
        new_lines = []
        lines = sent.split('\n')
        for line in lines:
            if line[0] == '#':
                new_lines.append(line)
                continue
            parts = line.split('\t')
            rnc_tags = get_rnc_tags(parts[2], parts[3], parts[5])
            parts[4] = rnc_tags
            line = '\t'.join(parts)
            new_lines.append(line)
        sents_with_rnc.append('\n'.join(new_lines))
    sents_with_rnc[0] = delete_body_tag(sents_with_rnc[0], closing=False)
    sents_with_rnc[-1] = delete_body_tag(sents_with_rnc[-1], closing=True)
    return sents_with_rnc


def transform_pipeline(text, f_path):
    sents = add_rnc_and_fix(text)
    ext_synt_sents = RNC_to_UD_add_ext_synt.mark_all(sents)
    hyphens = ['-', '--', '‑', '–', '—']
    ext_synt_sents = add_we_to_disjointed(ext_synt_sents, hyphens)
    # with open('result_files/mid_test.txt', 'w', encoding='utf-8', newline='\n') as f:
    #     f.write('\n\n'.join(ext_synt_sents))
    xml_sents = []
    some_stack = []
    for ind, sent in enumerate(ext_synt_sents):
        sent, meta = delete_meta_lines(sent)
        xml_sent, some_stack = transform_sent(sent, some_stack)
        xml_sents.append(xml_sent)
    if len(xml_sents) == 0:
        with open('Empty_texts_source.txt', 'a', encoding='utf-8') as f:
            f.write(f_path)
        return ''
    xml_text = '<?xml version="1.0" encoding="UTF-8"?><html>\n<head></head>\n<body>\n' + ''.join(xml_sents) + '\n</body></html>'
    return xml_text


def write_text(text, filepath, output_dir):
    conllu_name = '.'.join(filepath.split('.')[:-1]) + '.xml'
    os.makedirs(os.path.dirname(output_dir + conllu_name), exist_ok=True)
    with open(output_dir + conllu_name, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def main(root_dir, output_dir):
    walk = [(x, y, z) for x, y, z in os.walk(root_dir)]
    for root, dirs, files in tqdm(walk):
        for f in tqdm(files):
            f_path = os.path.join(root, f)
            with open(f_path, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f_path)
            new_text = transform_pipeline(text, f_path)
            if new_text != '':
                write_text(new_text, f_path, output_dir)


def process_file(paths):
    f_path, output_dir, error_file = paths
    with open(f_path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f_path)
    try:
        new_text = transform_pipeline(text, f_path)
        if new_text != '':
            write_text(new_text, f_path, output_dir)
    except:
        tb = traceback.format_exc()
        # with open('Pre1950_xml_errors.txt', 'a+', encoding='utf-8') as err_f:
        with open(error_file, 'a+', encoding='utf-8') as err_f:
            err_f.write('Error in ' + f_path + '\n')
            err_f.write(tb + '\n\n')
        print('ERROR:', f_path)
        print(tb)
    return f_path


def main_parallel(root_dir, output_dir, error_file):
    pool = mp.Pool(processes=mp.cpu_count())

    args = []
    walk = [(x, y, z) for x, y, z in os.walk(root_dir)]
    for root, dirs, files in tqdm(walk):
        for f in tqdm(files):
            f_path = os.path.join(root, f)
            args.append((f_path, output_dir, error_file))

    chunksize = min(len(args) // mp.cpu_count(), 15)
    for result in tqdm(pool.imap(func=process_file, iterable=args, chunksize=chunksize), total=len(args)):
        print('Done:', result)
    pool.close()

# if __name__ == '__main__':
#     root_dir = '..\\data_prediction\\source\\pre1950\\xviii'
#     output_dir = 'output\\'
#     main_parallel(root_dir, output_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    parser.add_argument('--errors', type=str, required=True)
    args = parser.parse_args()

    root_dir = args.root
    output_dir = args.output
    error_file = args.errors
    main_parallel(root_dir, output_dir, error_file)

# with open('test_files/emin_razmyshl_03.conllu', 'r', encoding='utf-8') as f:
#     text = f.read()
# new_text = transform_pipeline(text, 'lll')
# with open('test_files/emin_razmyshl_03.xml', 'w', encoding='utf-8', newline='\n') as f:
#     f.write(new_text)

# CURRENTLY USED VERSION 01.12
