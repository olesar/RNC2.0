import re
import RNC_to_UD_add_ext_synt
import os
from tqdm import tqdm
import multiprocessing as mp
import traceback
import html
from copy import deepcopy
import mystem_ext


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


tags_dict = get_RNCtoUD_table('data_lists/RNCtoUDtable-ext.txt')


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
            print('Not in list:', gram)
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
    infos = re.findall('"(.+?)"', tags)
    infos_escaped = [html.escape(inf) for inf in infos]
    for i in range(len(infos)):
        tags = tags.replace(infos[i], infos_escaped[i])
    return tags


# Пока неактуально
def collect_misc_info(line):
    parts = line.split('\t')
    misc = parts[9].split('|')
    spaces = '\n'
    close_tags = ''
    open_tags = ''
    word_form = ''
    for i in range(len(misc)):
        if misc[i].startswith('before='):
            open_tags = misc[i].replace('before=', '')
            open_tags = escape_tag_params(open_tags)
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
    if '\n\n' in spaces and ('</p>' in close_tags or '</speech>' in close_tags):
        spaces = spaces.replace('\n\n', '', 1)
    return open_tags, close_tags, spaces, word_form


# Пока неактуально
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


def add_to_stack(before_tags, after_tags, some_stack):
    tags = separate_tags(before_tags + after_tags)
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


def transform_sent(sent, some_stack):
    new_lines = []
    f_ana = '<ana lex="{}" gr="{}"{}></ana>' # '' in the last if no word_form
    f_word = '<w flags="{}">{}{}{}</w>'
    lines = sent.split('\n')
    tags_to_open = ''
    for tag in some_stack:
        tags_to_open += tag
    for i, line in enumerate(lines):
        info = get_word_info(line)
        mext = mystem_ext.extend_by_mystem(info)
        open_tags, close_tags, space_after, word_form = collect_misc_info(line)
        # if ('<p' in open_tags or '<speech' in open_tags) and i != 0:
        #     print('WARNING! Opens in sent!')
        # if ('</p>' in close_tags or '</speech' in close_tags) and i != len(lines) - 1:
        #     print('WARNING! Closes in sent')
        if info['pos'] == 'SYM' or info['pos'] == 'PUNCT':
            new_line = html.escape(info['lex'][0])
            if i > 0:
                new_lines[i-1] = new_lines[i-1].strip()
            elif i == 0:
                new_line = new_line.strip()
            some_stack = add_to_stack(open_tags, close_tags, some_stack)
            if i != 0:
                tags_to_open = ''
            new_lines.append(tags_to_open + open_tags + new_line + close_tags + space_after)
        else:
            ana_lines = []
            for j, gr in enumerate(info['gr']):
                if 'Hyph=Yes' not in line:
                    if word_form:
                        ana = f_ana.format(info['lex'][j], gr, ' wf="{}"'.format(word_form))
                    else:
                        ana = f_ana.format(info['lex'][j], gr, '')
                else:
                    if word_form:
                        ana = f_ana.format(info['lex'][j], gr + '" joined="hyphen', ' wf="{}"'.format(word_form))
                    else:
                        ana = f_ana.format(info['lex'][j], gr + '" joined="hyphen', '')
                ana_lines.append(ana.replace('  ', ' '))
            whole_ana = ''.join(ana_lines)
            word_line = f_word.format(info['synt'], whole_ana, mext, info['token'])
            some_stack = add_to_stack(open_tags, close_tags, some_stack)
            if i != 0:
                tags_to_open = ''
            new_line = tags_to_open + open_tags + word_line + close_tags + space_after
            new_lines.append(new_line)
    for tag in some_stack:
        tag_name = some_stack[-1].split()[0][1:]
        if tag_name[-1] == '>':
            tag_name = tag_name[:-1]
        close_pair = '</{}>'.format(tag_name)
        new_lines[-1] = new_lines[-1] + close_pair
    new_sent = '<se>\n' + ''.join(new_lines) + '</se>' + '\n\n'
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
    sents = text.split('\n\n')
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
    f_path, output_dir = paths
    with open(f_path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f_path)
    try:
        new_text = transform_pipeline(text, f_path)
        if new_text != '':
            write_text(new_text, f_path, output_dir)
    except:
        tb = traceback.format_exc()
        with open('Errors_on_source_to_xml.txt', 'a+', encoding='utf-8') as err_f:
            err_f.write('Error in ' + f_path + '\n')
            err_f.write(tb + '\n\n')
        print('ERROR:', f_path)
        print(tb)
    return f_path


def main_parallel(root_dir, output_dir):
    pool = mp.Pool(processes=mp.cpu_count())

    args = []
    walk = [(x, y, z) for x, y, z in os.walk(root_dir)]
    for root, dirs, files in tqdm(walk):
        for f in tqdm(files):
            f_path = os.path.join(root, f)
            args.append((f_path, output_dir))

    chunksize = min(len(args) // mp.cpu_count(), 15)
    for result in tqdm(pool.imap(func=process_file, iterable=args, chunksize=chunksize), total=len(args)):
        print('Done:', result)
    pool.close()

# if __name__ == '__main__':
#     root_dir = 'source_qbic_upd\\post1950'
#     output_dir = 'SOURCEtoXML\\'
#     main_parallel(root_dir, output_dir)

with open('test/test.conllu', 'r', encoding='utf-8') as f:
    text = f.read()
new_text = transform_pipeline(text, 'lll')
with open('xmlconllu/test.xml', 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_text)

# if no SpaceAfter - only \n or \s\n?
# break tags between sents and then continue them
# внутри <ana> в атрибут wf="" записывается distort-форма из графы 10.

