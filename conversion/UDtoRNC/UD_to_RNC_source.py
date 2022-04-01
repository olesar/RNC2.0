import re
import RNC_to_UD_add_ext_synt
import os
from tqdm import tqdm
import multiprocessing as mp
import traceback


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


tags_dict = get_RNCtoUD_table('RNCtoUDtable-ext.txt')


def get_rnc_pos(ud_pos, ud_gram, tags_dict, lex):
    rnc_pos = tags_dict[ud_pos]
    if ud_pos == 'PROPN' and 'Abbr=Yes' not in ud_gram:
        rnc_pos = 'S'
    elif lex == 'один' and ud_pos == 'NUM':
        rnc_pos = tags_dict['ANUM']
    elif lex == 'который':
        rnc_pos = 'APRO'
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


# Пока неактуально
def fix_misc(line):
    parts = line.split('\t')
    misc = parts[9].split('|')
    fixed_misc = []
    for i in range(len(misc)):
        if misc[i].startswith('after=') or misc[i].startswith('before='):
            fixed_misc.append(misc[i].replace(',', '').replace("'", '"'))
        if misc[i] == 'SpacesAfter=_':
            if len(misc) == 1:
                fixed_misc.append('_')
    parts[9] = '|'.join(fixed_misc)
    return '\t'.join(parts)


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
        break
    return '\n'.join(lines)

# Пока неактуально
# sents_with_rnc[0] = delete_body_tag(sents_with_rnc[0], closing=False)
# sents_with_rnc[-1] = delete_body_tag(sents_with_rnc[-1], closing=True)

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
    info_dict['token'] = parts[1]
    info_dict['pos'] = parts[3]
    info_dict['gr'], info_dict['lex'] = make_rnc_gram_lemmas(parts[4], parts[2])
    if parts[8] != '_':
        info_dict['synt'] = parts[7] + ',' + parts[8].replace('|', ',')
    else:
        info_dict['synt'] = parts[7]
    return info_dict


def transform_sent(sent):
    new_lines = []
    f_ana = '<ana lex="{}" gr="{}"></ana>'
    f_word = '<w flags="{}">{}{}</w>'
    lines = sent.split('\n')
    for i, line in enumerate(lines):
        info = get_word_info(line)
        if info['pos'] == 'SYM' or info['pos'] == 'PUNCT':
            new_line = info['lex'][0] + '\n'
            if i > 0:
                new_lines[i-1] = new_lines[i-1].strip()
            elif i == 0:
                new_line = new_line.strip()
            new_lines.append(new_line)
        else:
            ana_lines = []
            for j, gr in enumerate(info['gr']):
                if 'Hyph=Yes' not in line:
                    ana = f_ana.format(info['lex'][j], gr)
                else:
                    ana = f_ana.format(info['lex'][j], gr + '" joined="hyphen')
                ana_lines.append(ana.replace('  ', ' '))
            whole_ana = ''.join(ana_lines)
            word_line = f_word.format(info['synt'], whole_ana, info['token'])
            new_line = word_line + '\n'
            new_lines.append(new_line)
    return ''.join(new_lines)


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
    new_t = text.replace('\n~', '\n')
    new_t = new_t.replace('\n~', '\n')
    sents = new_t.split('\n\n\n\n')
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
            line = fix_misc(line)
            new_lines.append(line)
        sents_with_rnc.append('\n'.join(new_lines))
    return sents_with_rnc


def filter_sents_with_p(sents):
    normal_sents = []
    for sent in sents:
        sent_part = '\n'.join(sent.split('\n')[:-1])
        if '</p>' in sent_part:
            continue
        normal_sents.append(sent)
    return normal_sents


def transform_pipeline(text, f_path):
    sents = add_rnc_and_fix(text)
    filter_sents_with_rnc = filter_sents_with_p(sents)
    ext_synt_sents = RNC_to_UD_add_ext_synt.mark_all(filter_sents_with_rnc)
    xml_sents = []
    for sent in ext_synt_sents:
        sent, meta = delete_meta_lines(sent)
        xml_sent = '<se>\n' + transform_sent(sent) + '</se>\n'
        xml_sents.append(xml_sent)
    if len(xml_sents) == 0:
        with open('Empty_texts_source.txt', 'a', encoding='utf-8') as f:
            f.write(f_path)
        return ''
    xml_text = '<html>\n<head></head>\n<body>\n' + ''.join(xml_sents) + '\n</body></html>'
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
        with open('Errors_on_source_qbic.txt', 'a+', encoding='utf-8') as err_f:
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
