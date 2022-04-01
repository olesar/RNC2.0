

with open('pred_pos.txt', 'r', encoding='utf-8') as f:
    pred_text = f.read()
pred_lines = pred_text.split('\n')
pred_dict = {line.split('\t')[0]:line.split('\t')[1] for line in pred_lines}


def add_feat(feat, parts):
    if parts[5] == '_':
        parts[5] = feat
        return parts
    grams = parts[5].split('|')
    grams.append(feat)
    grams = sorted(grams, key=lambda x: x.lower())
    parts[5] = '|'.join(grams)
    return parts


def remove_pos(parts):
    if parts[3] == 'ANUM':
        if parts[2] == 'один':
            parts[3] = 'NUM'
        else:
            parts[3] = 'ADJ'
            parts = add_feat('Degree=Pos', parts)
    elif parts[3] == 'ADVPRO':
        parts[3] = 'ADV'
    elif parts[3] == 'PREDPRO':
        parts[3] = 'VERB'
    elif parts[3] == 'PARENTH':
        parts[3] = 'ADV'
    elif parts[3] == 'PRED':
        if parts[2].lower() not in pred_dict:
            parts[3] = 'ADJ'
        else:
            parts[3] = pred_dict[parts[2].lower()]
            if parts[3] == 'VERB':
                parts[5] = '_'
    elif parts[3] == 'INIT':
        parts[3] = 'PROPN'
    elif parts[3] == 'COM':
        parts[3] = 'ADJ'
    return parts


def remove_feats(parts):
    if parts[5] != '_':
        grams = parts[5].split('|')
        remove_grams = []
        for i, gram in enumerate(grams):
            if parts[3] == 'VERB' and 'PronType' in gram:
                remove_grams.append(gram)
            if 'Transit' in gram or 'Indecl' in gram:
                remove_grams.append(gram)
            elif ('Loc2' in gram) or ('Imp2' in gram) or ('Cmp2' in gram) or ('Acc2' in gram) \
                    or ('Number=Count'):
                grams[i] = gram.replace('Loc2', 'Loc').replace('Imp2', 'Imp').replace('Cmp2', 'Cmp')
                grams[i] = gram.replace('Acc2', 'Acc').replace('Number=Count', 'Number=Sing')
        for r_g in remove_grams:
            while r_g in grams:
                grams.remove(r_g)
        if not grams:
            parts[5] = '_'
        else:
            parts[5] = '|'.join(grams)
    return parts


def remove_gram(parts, grams, feat):
    if parts[5].count(feat) > 1:
        for gram in grams:
            if feat in gram:
                grams.remove(gram)
                break
    return grams


# fix errors seen in GramEval
def remove_doubles(parts):
    if parts[5] == '_':
        return parts
    grams = parts[5].split('|')
    feats = ['Case', 'Degree', 'Mood']
    for feat in feats:
        grams = remove_gram(parts, grams, feat)
    parts[5] = '|'.join(grams)
    return parts


def remove_ext(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    sents = text.split('\n\n')[:-1]
    for i, sent in enumerate(sents):
        lines = sent.split('\n')
        for j, line in enumerate(lines):
            if line[0] == '#':
                continue
            parts = line.split('\t')
            parts = remove_pos(parts)
            parts = remove_feats(parts)
            parts = remove_doubles(parts)
            lines[j] = '\t'.join(parts)
        sents[i] = '\n'.join(lines)
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        f.write('\n\n'.join(sents) + '\n\n')


remove_ext('taiga/ru_taiga-ud-dev.txt',
           'taiga_base/ru_taiga-ud-dev.txt')

