import conllu

taiga_files = ['Taiga/ru_taiga-ud-test.conllu',
               'Taiga/ru_taiga-ud-dev.conllu',
               'Taiga/002_ru_taiga-ud-train.conllu',
               'Taiga/001_ru_taiga-ud-train.conllu']

grameval_files = ['GramEval/GramEval_wo17taiga_train_ext.conllu',
                  'GramEval/GramEval_wo17taiga_dev_ext.conllu']


def get_gram_list(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    parsed = conllu.parse(text)

    all_grams = []
    for sent in parsed:
        for token in sent:
            pos = token['upostag']
            full_feats = []
            full_feats.append(pos)
            if token['feats']:
                for key in token['feats']:
                    add = key + '=' + token['feats'][key]
                    full_feats.append(add)
            all_grams.append('|'.join(full_feats))
    return all_grams


def get_grams_set(files_list, filename):
    full_gram_list = []
    for file in files_list:
        new_list = get_gram_list(file)
        full_gram_list.extend(new_list)
    full_gram_list = sorted(list(set(full_gram_list)))
    print(len(full_gram_list))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(full_gram_list))


# get_grams_set(taiga_files, 'Taiga_grams.txt')
# get_grams_set(taiga_files, 'GramEval_grams.txt')

# Taiga 1684
# GramEval 1684

with open('GramEval_grams.txt', 'r', encoding='utf-8') as f:
    grameval = f.read()
grameval_list = set(grameval.split('\n'))

with open('Taiga_grams.txt', 'r', encoding='utf-8') as f:
    taiga = f.read()
taiga_list = set(taiga.split('\n'))

# in GramEval, but not in Taiga
dif = grameval_list - taiga_list
with open('new_GramEval.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(list(dif))))
print(len(dif))

# in Taiga, but not in GramEval
dif = taiga_list - grameval_list
with open('not_in_GramEval.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(list(dif))))
print(len(dif))
