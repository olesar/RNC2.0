import re

# filepath = 'marx_split_result.conllu'
# with open(filepath, 'r', encoding='utf-8') as f:
#     text = f.read()

def delete_se_tag(line, closing):
    addition = 'before='
    tag = '<se>'
    if closing:
        addition = 'after='
        tag = '</se>'
    parts = line.split('\t')
    if parts[9] != addition + tag:
        parts[9] = parts[9].replace(tag, '')
    else:
        parts[9] = '_'
    line = '\t'.join(parts)
    return line


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


def change_sent_id(text):
    sents = text.split('\n\n')[:-1]
    for i in range(len(sents)):
        sents[i] = re.sub(r'# sent_id = \d+', '# sent_id = {}'.format(str(i + 1)), sents[i])
    new_text = '\n\n'.join(sents) + '\n\n'
    return new_text


def find_all_splits(text):
    split_dict = {}
    sents = text.split('\n\n')
    for i, sent in enumerate((sents[:-1])):
        lines = sent.split('\n')
        last_line = lines[-1]
        parts = last_line.split('\t')
        if parts[1] == ':' and 'p class=' not in parts[9]:
            if i == len(sents) - 2:
                continue
            next_sent = sents[i + 1]
            next_text = re.search('# text = (.+)', next_sent).group(1)
            next_lines = next_sent.split(next_text)[1].strip().split('\n')
            text = re.search('(# text = (.+))', sent).group()
            new_text = text + ' ' + next_text
            lines[-1] = delete_se_tag(lines[-1], closing=True)
            sent = '\n'.join(lines)
            next_lines[0] = delete_se_tag(next_lines[0], closing=False)
            new_whole_sent = sent.replace(text, new_text) + '\n' + '\n'.join(next_lines)
            new_whole_sent = change_numbers(new_whole_sent)
            replace_part = sents[i] + '\n\n' + sents[i + 1]
            split_dict[replace_part] = new_whole_sent
    return split_dict


def join_text_sents(text):
    split_dict = find_all_splits(text)
    for part in split_dict.keys():
        text = text.replace(part, split_dict[part])
    text = change_sent_id(text)
    return text

# split_text = join_text_sents(text)
#
# filepath = 'marx_join_result.conllu'
# with open(filepath, 'w', encoding='utf-8') as f:
#     f.write(split_text)
