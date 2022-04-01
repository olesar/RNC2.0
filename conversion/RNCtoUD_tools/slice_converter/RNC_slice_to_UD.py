import re
from bs4 import BeautifulSoup
from string import whitespace
import os


less_symb_replacer = chr(17)


def get_RNCtoUD_table(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tags_table = f.read()
    tags = tags_table.split('\n')
    tags_dict = {}
    for tag in tags:
        if tag != '':
            parts = tag.split('\t')
            tags_dict[parts[0]] = parts[1]
    return tags_dict


def get_list_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    some_list = text.split('\n')
    return some_list


tags_dict = get_RNCtoUD_table('data_lists/RNCtoUDtable-ext.txt')
cconj_list = get_list_from_file('data_lists/CCONJ_list.txt')
sym_list = get_list_from_file('data_lists/symbols_with_xml.txt')


def get_sents(text):
    body_text = re.search('<body>(.+)</body>', text, re.DOTALL)
    text = body_text.group(1).strip()
    xml_symbs = re.findall(r'&#\w+;', text)
    if xml_symbs != []:
        for s in xml_symbs:
            soup = BeautifulSoup(s)
            normal_s = soup.text
            if normal_s == '<':
                normal_s = less_symb_replacer
            text = text.replace(s, normal_s)
    sents = text.split('<se>')
    return sents


# Все, что связано со словами
def correct_distort(gr):
    if gr == 'distort':
        gr = 'S,distort'
    elif gr == '(distort)S,f,inan,nom,sg':
        gr = 'S,f,inan,nom,sg,distort'
    return gr


def get_word_info(word):
    soup = BeautifulSoup(word, 'html.parser')
    lemma = str(soup.text)
    ana = soup.findAll('ana')
    grams = []
    lexs = []
    for a in ana:
        lex = str(a.get('lex'))
        lexs.append(lex)
        gr = str(a.get('gr'))
        gr = correct_distort(gr)
        grams.append(gr.replace('=', ',').replace('-', ''))
    joined = str(ana[0].get('joined'))
    return lemma, lexs, grams, joined


def decide_pos(pos, grammems, lex, cconj_list):
    propn_grams = ['persn', 'famn', 'patrn', 'zoon', 'topon']
    if pos == 'V':
        if lex == 'быть':
            answer = 'AUX'
        else:
            answer = 'VERB'
    elif pos == 'CONJ':
        if lex.lower() in cconj_list:
            answer = 'CCONJ'
        else:
            answer = 'SCONJ'
    else:
        for g in propn_grams:
            if g in grammems:
                answer = 'PROPN'
                break
            else:
                answer = 'NOUN'
        if 'abbr' in grammems and lex[0].isupper():
            answer = 'PROPN'
    return answer


# Меняет помету части речи
def correct_pos(pos):
    correct_dict = {'PRO': 'PRON', 'ADPRO': 'ADVPRO', 'АPRO': 'APRO', 'n': 'APRO'}
    if pos in correct_dict.keys():
        pos = correct_dict[pos]
    return pos


def change_pos(pos, tags_dict, grammems, lex, cconj_list):
    double = ['V', 'CONJ', 'S']
    pos = correct_pos(pos)
    if pos in double:
        ud_pos = decide_pos(pos, grammems, lex, cconj_list)
    else:
        if lex == 'один' and pos == 'ANUM':
            ud_pos = 'NUM'
        elif lex == 'который':
            ud_pos = 'PRON'
        else:
            if pos == 'COM':
                ud_pos = 'COM'
            else:
                ud_pos = tags_dict[pos.strip()]
    return ud_pos


# Меняет грамматические пометы
def correct_gram(gram):
    correct_dict = {'ac0t': 'act', 'genm': 'gen', 'int': 'intr', 'inёan': 'inan', 'nm': 'nom', 'num': 'nom',
                    'PRAEDIC': ''}
    if gram in correct_dict.keys():
        gram = correct_dict[gram]
    return gram


def change_grammems(grammems, pos, tags_dict, ud_pos):
    cmp_pos = ['ADJ', 'ADV', 'PRED']
    ud_list = []
    for g in grammems:
        g = correct_gram(g)
        ud_g = tags_dict[g.strip()]
        if ud_g != '':
            ud_list.append(ud_g)
    if pos == 'INIT' and 'Abbr=Yes' not in ud_list:
        ud_list.append('Abbr=Yes')
    if 'Number=Count' in ud_list and 'Number=Sing' in ud_list:
        ud_list.remove('Number=Sing')
    if ud_pos == 'PROPN' and 'NameType' not in ''.join(ud_list):
        ud_list.append('NameType=Oth')
    if ud_pos in cmp_pos and 'Degree=Cmp' not in ud_list and 'Degree=Sup' not in ud_list:
        ud_list.append('Degree=Pos')
    ud_gram = '|'.join(sorted(ud_list, key=lambda x: x.lower()))
    return ud_gram


# Собирает линию с одним словом в новом формате
def make_word_line(word, k, cconj_list, tags_dict):
    word_ana = word.split('</w>')[0]
    lemma, lexs, grams, joined = get_word_info(word_ana)
    lex = lexs[0]
    gram = grams[0]
    if ',' in gram:
        pos = gram.split(',')[0]
        grammems = gram.split(',')[1:]
        ud_pos_temp = change_pos(pos, tags_dict, grammems, lex, cconj_list)
        ud_gram = change_grammems(grammems, pos, tags_dict, ud_pos_temp)
        if ud_gram == '':
            ud_gram = '_'
    else:
        pos = gram
        grammems = ''
        ud_gram = '_'
    rnc_grams = [g.replace(',', '.').replace(' ', '') + '.' for g in grams]
    for i in range(len(rnc_grams)):
        rnc_grams_list = rnc_grams[i].split('.')
        rnc_grams[i] = rnc_grams_list[0] + '.'.join(sorted(rnc_grams_list[1:])) + '.'
        rnc_grams[i] = lexs[i] + ':' + rnc_grams[i]
    rnc_gram = '|'.join(rnc_grams)
    if joined != 'None':
        ud_gram = ud_gram + '|' + joined
    ud_pos = change_pos(pos, tags_dict, grammems, lex, cconj_list)
    if ud_pos != 'SYM' and ud_pos != 'PUNCT':
        lemma = lemma.replace('`', '')
    line = str(k) + '\t' + lemma + '\t' + lex + '\t' + ud_pos + '\t' + rnc_gram + '\t' + ud_gram + '\t_' * 4
    return line


# собирает словарь с пунктуацией и тегами
def should_join(punct_1, punct_2):
    if punct_2 is None:
        punct_2 = 'None'
    if punct_1[-1] == punct_2 or punct_1[-1] in '?!' and punct_2 in '?!':
        return True
    return False


def join_same_punct(punct_with_tags):
    for i in range(1, len(punct_with_tags)):
        if len(punct_with_tags[i]['tags']) != 0:
            continue
        if should_join(punct_with_tags[i - 1]['punct'], punct_with_tags[i]['punct']):
            punct_with_tags[i]['punct'] = punct_with_tags[i - 1]['punct'] + punct_with_tags[i]['punct']
            punct_with_tags[i]['tags'] = punct_with_tags[i - 1]['tags']
            punct_with_tags[i - 1]['punct'] = 'deleted'
    return punct_with_tags


def remove_deleted(punct_with_tags):
    clear_punct_with_tags = []
    for i in range(len(punct_with_tags)):
        if punct_with_tags[i]['punct'] != 'deleted':
            clear_punct_with_tags.append(punct_with_tags[i])
    return clear_punct_with_tags


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
    punct_with_tags = join_same_punct(punct_with_tags)
    punct_with_tags = remove_deleted(punct_with_tags)
    return punct_with_tags


# Разрезает теги на before и текущие
def cut_tags(tags_list):
    open_tags = []
    for i, tag in enumerate(tags_list):
        name = re.search('</?(\w+).*', tag).group(1)
        if '/' in tag:
            if len(open_tags) == 0:
                continue
            if open_tags[-1][0] == name:
                open_tags.pop()
        else:
            open_tags.append((name, i))

    if len(open_tags) == 0:
        cut_index = len(tags_list)
    else:
        cut_index = open_tags[0][1]
    current = tags_list[cut_index:]
    prev = tags_list[:cut_index]
    return ''.join(prev), ''.join(current)


# Главное: трансформирует предложения
def transform_sents(sents, tags_dict, cconj_list, sym_list):
    new_sents = []
    tags_for_next = sents[0].strip().replace('\n', '\\n').replace('\t', '\\t')
    for sent in sents[1:]:
        all_lines = []
        tags_for_lines = []
        sent = sent.strip()
        words = sent.split('<w>')
        k = 1
        tags_for_next += '<se>'
        # --------------
        for word in words:
            if '</w>' in word:
                word_line = make_word_line(word, k, cconj_list, tags_dict)
                all_lines.append(word_line)
                k += 1
                tags_for_lines.append([])
                if tags_for_next != '':
                    tags_for_lines[-1].append('before=' + tags_for_next)
                    tags_for_next = ''
                after_word = word.split('</w>')[1]
            else:
                after_word = word

            punct_with_tags = split_punct_with_tags(after_word)

            for i, punct in enumerate(punct_with_tags[:-1]):  # потому что последний - None
                if punct['punct'][0] not in sym_list:
                    punct_line = str(k) + '\t' + punct['punct'] + '\t' + punct['punct'] + '\tPUNCT\tPUNCT.' + '\t_' * 5
                else:
                    punct_line = str(k) + '\t' + punct['punct'] + '\t' + punct['punct'] + '\tSYM\tSYM.' + '\t_' * 5
                all_lines.append(punct_line)
                k += 1
                tags_for_lines.append([])

                prev, curr = cut_tags(punct['tags'])
                if i == 0:  # потому что первому нужно добавить теги из предыдущего <se>
                    curr = tags_for_next + curr
                    tags_for_next = ''
                if curr:
                    tags_for_lines[-1].append('before=' + curr)
                if prev:
                    if len(tags_for_lines) > 1:
                        tags_for_lines[-2].append('after=' + prev)
                    else:
                        print('Unexpected!')
            prev, curr = cut_tags(punct_with_tags[-1]['tags'])
            if prev:
                if len(tags_for_lines) == 0:
                    added = False
                    prev_sent_tags = new_sents[-1][1][-1]
                    for k in range(len(prev_sent_tags)):
                        if 'after=' in prev_sent_tags[k]:
                            prev_sent_tags[k] += prev
                            added = True
                    if not added:
                        new_sents[-1][1][-1].append('after=' + prev)
                else:
                    tags_for_lines[-1].append('after=' + prev)
            tags_for_next = tags_for_next + curr
        new_sents.append((all_lines, tags_for_lines))
    result_sents = []
    for all_lines, tags_for_lines in new_sents:
        for i in range(len(all_lines)):
            if len(tags_for_lines[i]) > 0:
                all_lines[i] = all_lines[i][:-1] + '|'.join(tags_for_lines[i])
        result_sents.append('\n'.join(all_lines))
    return result_sents

# Составляет предложение без разбора
def next_is_punct(next_part):
    return next_part != '' and next_part.split('\t')[3] == 'PUNCT'


def make_sentence_from_parsed(parsed_sentence, cov):
    result = ''
    lines = parsed_sentence.split('\n')
    parsed_sent = parsed_sentence
    for i, line in enumerate(lines):
        space_after = False

        if line == '':
            continue
        parse_parts = line.split('\t')
        word = parse_parts[1]

        current_part = word
        with_space = ['(', '<', '{', '[', '«', '--']
        if word == '"':
            cov += 1

        if word in with_space or word == '"' and cov % 2 == 1:
            if word == '--':
                current_part += ' '
                space_after = True
        elif i < len(lines) - 1:
            if next_is_punct(lines[i + 1]):
                next_word = lines[i + 1].split('\t')[1]
                if next_word in with_space or next_word == '"' and cov % 2 == 0:
                    current_part += ' '
                    space_after = True
            else:
                if word != '-':
                    current_part += ' '
                    space_after = True
        result += current_part

        if i == len(lines) - 1:
            space_after = True
        if not space_after:
            parts = lines[i].split('\t')
            if parts[9] == '_':
                parts[9] = 'SpaceAfter=No'
            else:
                parts[9] = 'SpaceAfter=No' + '|' + parts[9]
            lines[i] = '\t'.join(parts)
        parsed_sent = '\n'.join(lines)

    result = result.replace('ё', 'е')
    result = result.replace('Ё', 'Е')
    return result.rstrip(), parsed_sent, cov


# Дополнительные изменения
# добавление пометы joined= в 10 столбик
# добавление пометы wf=  в 10 столбик
def move_joined(parts, joined_type):
    add_line = '|joined="' + joined_type[1:] + '"'
    if joined_type in parts[5]:
        parts[5] = parts[5].replace(joined_type, '')
        if parts[9] == '_':
            parts[9] = add_line[1:]
        else:
            parts[9] = parts[9] + '|' + add_line[1:]
    return parts


def move_word_form(parts, sym_type, replace_sym):
    if sym_type in parts[1]:
        if parts[9] == '_':
            parts[9] = 'wf=' + parts[1]
        else:
            parts[9] = parts[9] + '|' + 'wf=' + parts[1]
        if sym_type != '`':
            parts[1] = parts[1].replace(sym_type, replace_sym)
    return parts


def change_numbers(lines):
    for j, line in enumerate(lines):
        parts = line.split('\t')
        parts[0] = str(j + 1)
        lines[j] = '\t'.join(parts)
    return lines


def modify_space_after(parts):
    spaces = parts[9].split('|')
    for k in range(len(spaces)):
        if spaces[k].startswith('SpaceAfter'):
            spaces.pop(k)
            break
    for k in range(len(spaces)):
        if spaces[k].startswith('wf='):
            spaces[k] = spaces[k] + '.'
            break
    return spaces


### Присоединяет одиночные точки к предыдущему токену

def deal_with_dots(sent):
    pop_list = []
    lines = sent.split('\n')
    for i in range(len(lines[1:])):
        if lines[i].split('\t')[1] == '.':
            flag = True
            for j in range(i, len(lines)):
                if lines[j].split('\t')[3] != 'PUNCT' and lines[j].split('\t')[3] != 'SYM':
                    flag = False
            if not flag and i > 0:
                parts = lines[i - 1].split('\t')
                parts[1] = parts[1] + '.'
                if parts[9] == '_':
                    parts[9] = lines[i].split('\t')[9]
                else:
                    spaces = modify_space_after(parts)
                    parts[9] = '|'.join(spaces)
                    if lines[i].split('\t')[9] != '_':
                        if parts[9].strip() != '':
                            parts[9] = lines[i].split('\t')[9] + '|' + parts[9]
                        else:
                            parts[9] = lines[i].split('\t')[9]
                    elif parts[9] == '':
                        parts[9] = '_'
                lines[i - 1] = '\t'.join(parts)
                pop_list.append(i)

    for i in pop_list[::-1]:
        lines.pop(i)
    lines = change_numbers(lines)
    result = '\n'.join(lines)
    return result


def complete_transformation(new_sents):
    new_text = ''
    cov = 0     # счетчик кавычек
    modified_sents = []
    for k, sent in enumerate(new_sents):
        only_words_sent, space_sent, cov = make_sentence_from_parsed(sent, cov)
        lines = space_sent.split('\n')
        modified_lines = []
        for i in range(len(lines)):
            parts = lines[i].split('\t')
            parts = move_joined(parts, '|hyphen')
            parts = move_joined(parts, '|together')
            parts = move_word_form(parts, '`', '')
            parts = move_word_form(parts, 'ё', 'е')
            parts = move_word_form(parts, 'Ё', 'Е')
            lines[i] = '\t'.join(parts)
            modified_lines.append('\t'.join(parts))
        modified_sents.append('\n'.join(modified_lines))
        space_sent = '\n'.join(lines)
        space_sent = deal_with_dots(space_sent)
        # space_sent = add_fake_deps(space_sent)

        if k != 0:
            if '</p>' in modified_sents[k - 1].split('\n')[-1]:
                new_text = new_text + '# newpar\n# sent_id = ' + str(
                    k + 1) + '\n# text = ' + only_words_sent + '\n' + space_sent + '\n\n'
            else:
                new_text = new_text + '# sent_id = ' + str(
                    k + 1) + '\n# text = ' + only_words_sent + '\n' + space_sent + '\n\n'
        else:
            new_text = new_text + '# newdoc\n# sent_id = ' + str(
                k + 1) + '\n# text = ' + only_words_sent + '\n' + space_sent + '\n\n'
        new_text = new_text.replace(less_symb_replacer, '<')
    return new_text


def RNCtoUD_one_text(text, sym_list, cconj_list, tags_dict):
    comment_reg = re.findall(r'<!--.*?-->', text, re.DOTALL)
    if len(comment_reg) > 0:
        for comment in comment_reg:
            text = text.replace(comment, '')
    sents = get_sents(text)
    new_sents = transform_sents(sents, tags_dict, cconj_list, sym_list)
    new_text = complete_transformation(new_sents)
    return new_text


# files = os.listdir('C:\\Users\\Yana\\project\\corpus_slice')
# for f_name in files:
#     path = 'C:\\Users\\Yana\\project\\corpus_slice\\' + f_name
#     print(f_name)
#     with open(path, 'r', encoding='utf-8') as f:
#         text = f.read()
#     new_text = RNCtoUD_one_text(text, sym_list, cconj_list, tags_dict)
#     conllu_name = '.'.join(f_name.split('.')[:-1]) + '.conllu'
#     output_path = 'C:\\Users\\Yana\\project\\corpus_slice_conllu\\' + conllu_name
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(new_text)

