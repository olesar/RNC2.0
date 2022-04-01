from conllu import parse
from collections import OrderedDict


def get_info_table(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tags_table = f.read()
    tags = tags_table.split('\n')
    pos_dict = {}
    gram_dict = {}
    for tag in tags:
        parts = tag.split('\t')
        if '=' in tag:
            gram_dict[parts[0]] = parts[1]
        else:
            pos_dict[parts[0]] = parts[1]
    return pos_dict, gram_dict


def split_misc(key, value):
    misc = key[value].split('|')
    new_misc = OrderedDict()
    for m in misc:
        misc_key = m.split('=')[0]
        misc_value = '='.join(m.split('=')[1:])
        new_misc[misc_key] = misc_value
    return new_misc


def change_ext_tags(sent, pos_dict, gram_dict):
    for word in sent:
        if word['upostag'] in pos_dict.keys():
            basic_tag = pos_dict[word['upostag']]
            word['upostag'] = basic_tag
        if word['feats']:
            for gram in gram_dict.keys():
                gram_cat = gram.split('=')[0]
                gram_value = gram.split('=')[1]
                if gram_cat in word['feats'].keys() and word['feats'][gram_cat] == gram_value:
                    if gram_dict[gram] == '':
                        del word['feats'][gram_cat]
                    else:
                        word['feats'][gram_cat] = gram_dict[gram].split('=')[1]
    return sent


def convert_to_basic(text):
    pos_dict, gram_dict = get_info_table('data_lists\\UD-ext_to_UD-base_table.txt')
    sentences = parse(text, field_parsers={"misc": split_misc})
    for sent in sentences:
        new_sent = change_ext_tags(sent, pos_dict, gram_dict)
    basic_text = '\n\n'.join(sentence.serialize() for sentence in sentences)
    basic_text = basic_text.replace('\n\n\n\n', '\n\n')
    basic_text = basic_text.replace('_=', '_')
    return basic_text


# with open('marx_split_result.conllu', 'r', encoding='utf-8') as f:
#     text = f.read()
# basic_text = convert_to_basic(text)
# with open('marx_basic_ud.conllu', 'w', encoding='utf-8') as f:
#     f.write(basic_text)



# Anom=Yes Indecl=Yes - не убирается из ext
# Gender=Com - не добавляется в ext