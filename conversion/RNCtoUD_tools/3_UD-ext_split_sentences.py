from string import whitespace
import re

with open('data_lists/sent_split_list.txt', 'r', encoding='utf-8') as f:
    info_text = f.read()


def prepare_info(info_text):
    info_lines = info_text.split('\n')
    sent_info_lines = []
    for line in info_lines:
        if '<se>' in line:
            sent_info_lines.append(line.replace('<!/>', ' '))
    return sent_info_lines


def prepare_info_dict(sent_info):
    file_sent_dict = {}
    for info in sent_info:
        parts = info.split(' # text = ')
        file = parts[0].split(':')[0]
        sent = parts[1]
        if file not in file_sent_dict.keys():
            file_sent_dict[file] = [sent]
        else:
            file_sent_dict[file].append(sent)
    return file_sent_dict


sent_info = prepare_info(info_text)
info_dict = prepare_info_dict(sent_info)
# print(info_dict)
# /standard/texts/pre1950/xviii/fonvizin/fonviz_044.conllu
# if filename in info_dict.keys()

# filepath = 'C:\\Users\\Yana\\work_project\\RNCtoUD_result_4\\texts\\pre1950\\xx-1\\bulgakov_ma\\master1.xml'
# filepath = filepath.replace('\\', '/')
# file_part = filepath.split('/texts/')[-1]
filepath = 'RNCtoUD_result\\test_files_RNC\\marx-fixed.conllu'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()
# dummy_part = '/standard/texts/' + '.'.join(file_part.split('.')[:-1]) + '.conllu'
dummy_part = '/standard/texts/pre1950/xx-1/lenin/marx.conllu'
# dummy_part = '/standard/texts/pre1950/xviii/novikov/novikov_12.conllu'

split_sents = info_dict[dummy_part]


def find_split_index(split_sent, sent_for_split):
    split_sent2 = split_sent
    change_sent2 = sent_for_split
    change_index = 0
    while len(change_sent2) > 0 and len(split_sent2) > 0:
        if change_sent2[0] in whitespace:
            change_sent2 = change_sent2[1:]
            change_index += 1
            continue
        if split_sent2[0] in whitespace:
            split_sent2 = split_sent2[1:]
            continue
        if split_sent2[0] == change_sent2[0]:
            change_sent2 = change_sent2[1:]
            change_index += 1
            split_sent2 = split_sent2[1:]
        else:
            break
    return change_index


def split_text_sent(split_sent, sent_for_split, num_of_sents):
    sent_parts = []
    second_part = sent_for_split
    for i in range(num_of_sents):
        split_index = find_split_index(split_sent, second_part)
        split_sent = '</se> <se>'.join(split_sent.split('</se> <se>')[1:])
        first_part = second_part[:split_index].strip()
        second_part = second_part[split_index:].strip()
        sent_parts.append(first_part)
    sent_parts.append(second_part)
    return sent_parts


def find_line_index(text_sent_part, sent_lines):
    first_part2 = text_sent_part
    lines = sent_lines
    head_lines = []
    while len(first_part2) > 0:
        for i, line in enumerate(lines):
            if line[0] == '#':
                head_lines.append(line)
                continue
            parts = line.split('\t')
            if first_part2.startswith(parts[1]):
                first_part2 = first_part2[len(parts[1]):].strip()
            else:
                break
    return i, head_lines


def split_line_sent(text_sent_parts, lines_sent, num_of_sents):
    sent_parts = []
    lines = lines_sent.split('\n')
    for i in range(num_of_sents):
        split_index, head_lines = find_line_index(text_sent_parts[i], lines)
        if i == 0:
            main_head = '\n'.join(head_lines)
            first_part_head = re.sub('# text = .+', '# text = {}'.format(text_sent_parts[i]), main_head)
            whole_first_part = first_part_head + '\n' + '\n'.join(lines[len(head_lines):split_index])
        else:
            first_part_head = re.sub('# text = .+', '# text = {}'.format(text_sent_parts[i]), main_head.replace('# newpar\n', ''))
            whole_first_part = first_part_head + '\n' + '\n'.join(lines[:split_index])
        sent_parts.append(whole_first_part)
        lines = lines[split_index:]
    second_part_head = re.sub('# text = .+', '# text = {}'.format(text_sent_parts[-1]), main_head.replace('# newpar\n', ''))
    whole_second_part = second_part_head + '\n' + '\n'.join(lines)
    sent_parts.append(whole_second_part)
    return sent_parts

def change_numbers(sent):
    word_lines = sent.split('\n')
    count = 0
    for j, line in enumerate(word_lines):
        if line[0] == '#':
            continue
        parts = line.split('\t')
        count += 1
        parts[0] = str(count)
        word_lines[j] = '\t'.join(parts)
    new_sent = '\n'.join(word_lines)
    return new_sent


def add_tag(parts, tag, opening):
    added = False
    if parts[9] == '_':
        if not opening:
            parts[9] = 'after=' + tag
        else:
            parts[9] = 'before=' + tag
    elif '<' in parts[9]:
        spaces = parts[9].split('|')
        for i in range(len(spaces)):
            if not opening and '<' in spaces[i] and 'before' not in spaces[i]:
                spaces[i] += tag
                added = True
            if opening and '<' in spaces[i] and 'before' in spaces[i]:
                spaces[i] += tag
                added = True
        parts[9] = '|'.join(spaces)
    elif not added:
        if not opening:
            parts[9] = parts[9] + '|after=' + tag
        else:
            parts[9] = parts[9] + '|before=' + tag
    return parts


def add_se_tags(sent_parts):
    new_sents = []
    for i, sent in enumerate(sent_parts):
        lines = sent.split('\n')
        for j in range(len(lines)):
            if lines[j][0] != '#':
                first_line_ind = j
                break
        if i != 0:
            first_word_parts = lines[first_line_ind].split('\t')
            first_word_parts = add_tag(first_word_parts, '<se>', opening= True)
            lines[j] = '\t'.join(first_word_parts)
        if i != len(sent_parts) - 1:
            last_word_parts = lines[-1].split('\t')
            last_word_parts = add_tag(last_word_parts, '</se>', opening=False)
            lines[-1] = '\t'.join(last_word_parts)
        new_sents.append('\n'.join(lines))
    return new_sents


def same_sentence(split_sent, sent):
    punct = ')]}.!?»"\''
    orig_split_sent = split_sent
    split_sent = split_sent.strip()
    split_char = split_sent[0]
    text_sent = re.search('# text = (.*)', sent).group(1)
    while split_char in punct:
        if text_sent.strip().startswith(split_char):
            break
        split_sent = split_sent[1:]
        split_char = split_sent[0]
    clean_split_sent = split_sent.replace('</se> <se>', ' ')
    if clean_split_sent.replace(' ', '') in text_sent.replace(' ', ''):
        return split_sent, sent, True
    else:
        return orig_split_sent, sent,  False


def collect_sents_for_split(text):
    change_dict = {}
    text_sents = text.split('\n\n')[:-1]
    for split_sent in split_sents:
        for sent in text_sents:
            split_sent, sent, same = same_sentence(split_sent, sent)
            if same:
                sent_tags = re.findall('</se> <se>',split_sent)
                num_of_sents = len(sent_tags)
                sent_for_split = re.search('# text = (.+)\n', sent).group(1)
                text_sent_parts = split_text_sent(split_sent, sent_for_split, num_of_sents)
                whole_sent_parts = split_line_sent(text_sent_parts, sent, num_of_sents)
                whole_sent_parts = [change_numbers(sent) for sent in whole_sent_parts]
                whole_sent_parts = add_se_tags(whole_sent_parts)
                change_dict[sent] = '\n\n'.join(whole_sent_parts)
                break
    return change_dict


def change_sent_id(text):
    sents = text.split('\n\n')[:-1]
    for i in range(len(sents)):
        sents[i] = re.sub(r'# sent_id = \d+', '# sent_id = {}'.format(str(i + 1)), sents[i])
    new_text = '\n\n'.join(sents) + '\n\n'
    return new_text


def split_text_sents(text):
    new_text = text
    change_dict = collect_sents_for_split(text)
    for sent in change_dict.keys():
        new_text = new_text.replace(sent, change_dict[sent])
    new_text = change_sent_id(new_text)
    return new_text


new_text = split_text_sents(text)
with open('marx_split_result.conllu', 'w', encoding='utf-8') as f:
    f.write(new_text)


# CHECK LIST
# more than 1 split +
# re-numerate lines +
# delete #newpar if between sentences +
# add tag </se> in the end and before:<se> in the beginning +
# if first punct was moved - delete it +
# re-numerate sent_id +
