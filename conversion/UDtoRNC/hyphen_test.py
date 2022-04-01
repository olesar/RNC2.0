# 1 — слитно, 0 — раздельно, 12 — субтокенизация

# if 0: (раздельно) 0 - 1
# <we flags="...">
#   <ana lex="Дон-Кихот"></ana>
#   <w><ana lex="Дон" gr="..."/><anam .../>Дон</w>
#   -
#   <w><ana lex="Кихот" gr="..."/><anam .../>Кихот</w>
#
# </we>

# if 1: (слитно) 1 - 12
# <w flags="...">
#   <ana lex="бизнес-центр" gr="..."/>
#   <anam lex="бизнес-центр" gr="..."/>
#   <wi><ana lex="бизнес"/>бизнес</wi>-<wi><ana lex="центр"/>центре</wi>
# </w>

#газпром-нефти 1 - 0
# чем комбинации 1 - 0 отличаются от 1 - 12

# 47	исси-ле-мулино	0	1 - осн раздельно, доп слитно - we

import re

with open('data_lists/HyphenA-I.txt', 'r', encoding='utf-8') as f:
    text = f.read()
distort_dict = {}
lines = text.split('\n')[:-1]
for line in lines:
    parts = line.split('\t')
    if parts[3] != '_':
        distort_dict[parts[1]] = parts[2]

# with open('test_files/hyphen_test.txt', 'r', encoding='utf-8') as f:
#     text = f.read()
# sents = text.split('\n\n')[:-1]


# ADDS "WE" TO WORDS IN NEED OF <WE> TAG - NEED TO BE DISJOINTED
# находит разъединенные по дефису слова и соединяет их - для случаев 1 - 0
def fix_distort(sents, hyphens):
    new_sents = []
    for sent in sents:
        meta_lines = re.search('^(#.*\n)*', sent).group()
        no_meta_sent = sent[len(meta_lines):]
        lines = no_meta_sent.split('\n')
        new_lines = []
        i = 1
        seq = ''
        new_lines.append(lines[0])
        skipped = []
        while i < len(lines):
            parts = lines[i].split('\t')
            if parts[1] in hyphens \
                    and 'SpaceAfter=No' in parts[9] and 'SpaceAfter=No' in lines[i-1].split('\t')[9]:
                seq = seq + lines[i-1].split('\t')[1] + parts[1]
                skipped.append(lines[i-1])
                skipped.append(lines[i])
                i += 2
            else:
                if seq:
                    seq = seq + lines[i-1].split('\t')[1]
                    parts = lines[i - 1].split('\t')
                    if seq.lower() in distort_dict and distort_dict[seq.lower()] == '1':  # (осн напис слитно)
                        parts[1] = seq
                        if parts[9] == '_':
                            parts[9] = 'WI'
                        else:
                            parts[9] = parts[9] + '|WI'
                        new_lines.pop(-1)
                        new_lines.append('\t'.join(parts))
                        skipped = []
                    else:
                        new_lines.pop(-1)
                        new_lines.extend(skipped)
                        new_lines.append(lines[i-1])
                        skipped = []
                seq = ''
                new_lines.append(lines[i])
                i += 1
        if seq:
            seq = seq + lines[-1].split('\t')[1]
            parts = lines[-1].split('\t')
            if seq.lower() in distort_dict and distort_dict[seq.lower()] == '1':
                parts[1] = seq
                # parts[2] = seq лемму надо собирать отдельно!
                if parts[9] == '_':
                    parts[9] = 'WI'
                else:
                    parts[9] = parts[9] + '|WI'
                new_lines.pop(-1)
                new_lines.append('\t'.join(parts))
            else:
                new_lines.pop(-1)
                new_lines.extend(skipped)
                new_lines.append(lines[-1])
                skipped = []
        seq = ''
        new_sents.append(meta_lines + '\n'.join(new_lines))
    # print('\n\n'.join(new_sents))
    return new_sents


def add_wi_to_joined(parts):
    word = parts[1].lower()
    if '-' in word or '‑' in word or '–' in word or '—' in word:
        if word.lower() in distort_dict and distort_dict[word.lower()] == '1':
            if parts[9] == '_':
                parts[9] = 'WI=' + word
            else:
                parts[9] = parts[9] + '|WI=' + word
    return parts


def add_we_to_disjointed(sents, hyphens):
    new_sents = []
    for sent in sents:
        meta_lines = re.search('^(#.*\n)*', sent).group()
        no_meta_sent = sent[len(meta_lines):]
        lines = no_meta_sent.split('\n')
        new_lines = []
        i = 1
        seq = ''
        # add wi
        parts = lines[0].split('\t')
        parts = add_wi_to_joined(parts)
        lines[0] = '\t'.join(parts)
        # add wi
        new_lines.append(lines[0])
        skipped = False
        while i < len(lines):
            parts = lines[i].split('\t')
            if parts[1] in hyphens \
                    and 'SpaceAfter=No' in parts[9] and 'SpaceAfter=No' in lines[i-1].split('\t')[9]:
                if not seq:
                    starting = len(new_lines)
                seq = seq + lines[i-1].split('\t')[1] + parts[1]
                new_lines.append(lines[i-1])
                new_lines.append(lines[i])
                i += 2
            else:
                if seq:
                    skipped = True
                    seq = seq + lines[i-1].split('\t')[1]
                    parts = lines[i - 1].split('\t')
                    if seq.lower() in distort_dict and distort_dict[seq.lower()] == '0':  # (осн - раздельно)
                        new_lines.pop(starting)
                        starting_parts = new_lines[starting-1].split('\t')
                        if starting_parts[9] == '_':
                            starting_parts[9] = 'WE-START=' + seq
                        else:
                            starting_parts[9] = starting_parts[9] + '|WE-START=' + seq
                        new_lines[starting-1] = '\t'.join(starting_parts)
                        if parts[9] == '_':
                            parts[9] = 'WE-END=' + seq
                        else:
                            parts[9] = parts[9] + '|WE-END=' + seq
                        new_lines.append('\t'.join(parts))
                        # new_lines.append(lines[i])
                    else:
                        new_lines.pop(-2)
                        parts = lines[i-1].split('\t')
                        parts = add_wi_to_joined(parts)
                        lines[i-1] = '\t'.join(parts)
                        new_lines.append(lines[i-1])
                seq = ''
                # if not skipped:
                parts = lines[i].split('\t')
                parts = add_wi_to_joined(parts)
                lines[i] = '\t'.join(parts)
                new_lines.append(lines[i])
                i += 1
                skipped = False
        if seq:
            seq = seq + lines[-1].split('\t')[1]
            parts = lines[-1].split('\t')
            if seq.lower() in distort_dict and distort_dict[seq.lower()] == '0':
                new_lines.pop(starting-1)
                starting_parts = new_lines[starting-1].split('\t')
                if starting_parts[9] == '_':
                    starting_parts[9] = 'WE-START=' + seq
                else:
                    starting_parts[9] = starting_parts[9] + '|WE-START=' + seq
                new_lines[starting-1] = '\t'.join(starting_parts)
                if parts[9] == '_':
                    parts[9] = 'WE-END=' + seq
                else:
                    parts[9] = parts[9] + '|WE-END=' + seq
                new_lines.append('\t'.join(parts))
            else:
                new_lines.pop(starting - 1)
                parts = lines[-1].split('\t')
                parts = add_wi_to_joined(parts)
                lines[-1] = '\t'.join(parts)
                new_lines.append(lines[-1])
        seq = ''
        new_sents.append(meta_lines + '\n'.join(new_lines))
    # print('\n\n'.join(new_sents))
    return new_sents

hyphens = ['-', '--', '‑', '–', '—']
# new_sents = fix_distort(sents, hyphens)
# add_we_to_disjointed(sents, hyphens)


