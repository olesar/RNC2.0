import re


# Проверяет наличие субъекта: с субъектом - новая клауза, без субъекта - однородные
# True - у слова есть субъект, False - субъекта нет
def find_nsubj(num, lines):
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[6] == num and 'nsubj' in parts[7]:
            return True
    return False


# Проверяет формы глаголов по числу и роду, чтобы определить, могут ли они быть однородными
def check_conj_form(root_parts, conj_parts):
    if 'Gender' in root_parts[5]:
        conj_match_1 = re.search('Gender=\w+', conj_parts[5])
        root_match_1 = re.search('Gender=\w+', root_parts[5])
        conj_match_2 = re.search('Number=\w+', root_parts[5])
        root_match_2 = re.search('Number=\w+', root_parts[5])
        if conj_match_1 and conj_match_2:
            if root_match_1.group() != conj_match_1.group() or root_match_2.group() != conj_match_2.group():
                return True
    elif 'Person' in root_parts[5]:
        conj_match_1 = re.search('Person=\w+', conj_parts[5])
        root_match_1 = re.search('Person=\w+', root_parts[5])
        conj_match_2 = re.search('Number=\w+', root_parts[5])
        root_match_2 = re.search('Number=\w+', root_parts[5])
        if conj_match_1 and conj_match_2:
            if root_match_1.group() != conj_match_1.group() or root_match_2.group() != conj_match_2.group():
                return True
    return False


# Проверяет является ли однородное отдельной клаузой.
# True - новая клауза, False - текущая клауза
def check_conj(conj_parts, root_parts, lines):
    same = ['NOUN', 'PRON', 'PROPN']
    if conj_parts[3] == root_parts[3] or (conj_parts[3] in same and root_parts[3] in same): # Тут
        if find_nsubj(conj_parts[0], lines):
            return True
        else:
            if conj_parts[3] == 'VERB' and check_conj_form(root_parts, conj_parts):
                return True
            return False
    else:
        return True


# Все условия: слово принадлежит текущей клаузе или относится к другой?
# True - текущая клауза, False - другая клауза
def conditions(parts, sent, root_parts):
    check_marks = ['acl', 'advcl', 'conj', 'parataxis']
    clause_marks = ['acl:relcl', 'ccomp']
    if parts[7] in clause_marks:
        return False
    elif parts[7] in check_marks:
        # if parts[7] == 'advcl' and 'VerbForm=Conv' not in parts[5]:
        if parts[7] == 'advcl':
            return False
        if parts[7] == 'acl':
            if 'VerbForm=Part' not in parts[5] and parts[3] != 'ADJ' or sent.find('\t' + parts[0] + '\tmark') != -1:
                return False
        if parts[7] == 'conj':
            if check_conj(parts, root_parts, sent.split('\n')):
                return False
        if parts[7] == 'parataxis' and (find_nsubj(parts[0], sent.split('\n')) or parts[3] == 'VERB'):
            return False
    return True


# Находит все слова клаузы
def find_all_children(lines, root):
    children = []
    root_parts = root.split('\t')
    root_num = root_parts[0]
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[6] == root_num and conditions(parts, '\n'.join(lines), root_parts):
            children.append(parts[0])
            children.extend(find_all_children(lines, lines[i]))
    return children


# Добавляет помету слову
def mark_children(children, lines, mark):
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[0] in children:
            if parts[8] == '_':
                parts[8] = mark
            else:
                parts[8] = parts[8] + '|' + mark
        lines[i] = '\t'.join(parts)
    return lines


# Добавляет помету всем словам клаузы
def mark_whole_clause(lines, root, mark):
    children = find_all_children(lines, root)
    lines = mark_children(children, lines, mark)
    return lines


def mark_children_gerp_partp(children, lines, mark):
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[0] in children:
            if parts[8] == '_':
                parts[8] = mark
            else:
                if 'clause_subj' in parts[8] or 'clause_main' in parts[8]:
                    parts[8] = parts[8].replace('clause_subj', mark).replace('clause_main', mark)
                else:
                    parts[8] = parts[8] + '|' + mark
        lines[i] = '\t'.join(parts)
    return lines


def mark_whole_clause_gerp_partp(lines, root, mark):
    children = find_all_children(lines, root)
    lines = mark_children_gerp_partp(children, lines, mark)
    return lines


# Добавление помет clause_subj клаузам с вершинами acl, advcl, parataxis
# Вершина не может быть причастием и прилагательным. Или должен быть союз, зависимый от вершины.
def mark_acl(sent):
    if sent.find('acl') != -1:
        lines = sent.split('\n')
        for i in range(len(lines)):
            parts = lines[i].split('\t')
            if len(parts) > 1 and parts[7] == 'acl':
                acl_num = parts[0]
                if 'VerbForm=Part' not in parts[5] and parts[3] != 'ADJ' or sent.find('\t' + str(acl_num) + '\tmark') != -1:
                    parts[8] = 'clause_subj'
                    lines[i] = '\t'.join(parts)
                    lines = mark_whole_clause(lines, lines[i], 'clause_subj')
                    sent = '\n'.join(lines)
                elif 'VerbForm' in parts[5] and sent.find('\t' + parts[0] + '\t') != -1:
                    parts[8] = 'partp'
                    lines[i] = '\t'.join(parts)
                    lines = mark_whole_clause_gerp_partp(lines, lines[i], 'partp')
                    sent = '\n'.join(lines)
    return sent

# Вершина не может быть деепричастием.
def mark_advcl(sent):
    if sent.find('advcl') != -1:
        lines = sent.split('\n')
        for i in range(len(lines)):
            parts = lines[i].split('\t')
            if len(parts) > 1 and parts[7] == 'advcl':
                if 'VerbForm=Conv' not in parts[5]:
                    parts[8] = 'clause_subj'
                    lines[i] = '\t'.join(parts)
                    lines = mark_whole_clause(lines, lines[i], 'clause_subj')
                    sent = '\n'.join(lines)
                else:
                    parts[8] = 'gerp'
                    lines[i] = '\t'.join(parts)
                    lines = mark_whole_clause_gerp_partp(lines, lines[i], 'gerp')
                    sent = '\n'.join(lines)
    return sent

# Вершина либо должна быть глаголом, либо иметь субъект.
def mark_parataxis(sent):
    if sent.find('parataxis') != -1:
        lines = sent.split('\n')
        for i in range(len(lines)):
            parts = lines[i].split('\t')
            if len(parts) > 1 and parts[7] == 'parataxis':
                if find_nsubj(parts[0], lines) or parts[3] == 'VERB':
                    parts[8] = 'clause_subj'
                    lines[i] = '\t'.join(parts)
                    lines = mark_whole_clause(lines, lines[i], 'clause_subj')
                    sent = '\n'.join(lines)
    return sent


# Разметка эллипсиса - помета только на вершине слова с зависимостью orphan
def mark_ellipsis(sents):
    new_sents = []
    for sent in sents:
        if sent.find('orphan') == -1:
            new_sents.append(sent)
            continue
        else:
            lines =  sent.split('\n')
            for line in lines:
                parts = line.split('\t')
                if len(parts) > 1 and parts[7] == 'orphan':
                    root_num = parts[6]
            for i in range(len(lines)):
                parts = lines[i].split('\t')
                if len(parts) > 1 and parts[0] == root_num:
                    if parts[8] != '_':
                        parts[8] = parts[8] + '|ellipsis'
                    else:
                        parts[8] = 'ellipsis'
                    lines[i] = '\t'.join(parts)
            new_sent = '\n'.join(lines)
            new_sents.append(new_sent)
    return new_sents


# Определение типа клаузы: v, nom, predicative
# Краткие прилагательные без субъекта - предикативы
def check_short_form(parts, lines):
    if 'Variant=Short' in parts[5]:
        if find_nsubj(parts[0], lines):
            return 'clause_nom'
        else:
            return 'predicative'
    else:
        return 'clause_nom'


# Определяет тип клаузы по части речи и всем остальным параметрам
def check_pos(parts, lines):
    main_part = parts[3]
    nom = ['ADJ', 'NOUN', 'PRON', 'PROPN', 'NUM', 'ANUM', 'DET']
    v = ['VERB']
    pred = ['ADV']
    if main_part in nom:
        if main_part == 'ADJ':
            return check_short_form(parts, lines)
        else:
            return 'clause_nom'
    elif main_part in v:
        # полные причастия - именная группа, остальное - глагольная
        if 'VerbForm=Part' in parts[5] and 'Variant=Short' not in parts[5]:
            return 'clause_nom'
        else:
            return 'clause_v'
    elif main_part in pred:
        return 'predicative'
    else:
        return False


# Отдельно размечает однородные клаузы
def find_conj(conj_num, lines, root_parts):
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[6] == conj_num and parts[7] == 'conj':
            if check_conj(parts, root_parts, lines):
                mark = check_pos(parts, lines)
                if mark:
                    parts[8] = mark
                    lines[i] = '\t'.join(parts)
                    lines = mark_whole_clause(lines, lines[i], mark)
    return lines


# Добавление всех помет clause: v, nom, predicative
# Отдельные условия для главных клауз, придаточных, паратаксиса и однородных клауз
def mark_clause_type(sent):
    roots = ['root', 'acl:relcl', 'ccomp']
    other_roots = ['acl', 'advcl']

    lines = sent.split('\n')
    for i in range(len(lines)):
        parts = lines[i].split('\t')

        if len(parts) > 1 and parts[7] in roots and '<' not in parts[1]:
            mark = check_pos(parts, lines)
            if mark:
                if parts[8] != '_':
                    parts[8] = parts[8] + '|' + mark
                else:
                    parts[8] = mark
                lines[i] = '\t'.join(parts)
                lines = find_conj(parts[0], lines, parts)
                lines = mark_whole_clause(lines, lines[i], mark)

        elif len(parts) > 1 and parts[7] in other_roots and '<' not in parts[1]:
            if sent.find(parts[0] + '\tmark') != -1 or \
                    (parts[7] == 'acl' and 'VerbForm=Part' not in parts[5] and parts[3] != 'ADJ') or \
                        (parts[7] == 'advcl'):
                        # (parts[7] == 'advcl' and 'VerbForm=Conv' not in parts[5])
                mark = check_pos(parts, lines)
                if mark:
                    if parts[8] != '_':
                        parts[8] = parts[8] + '|' + mark
                    else:
                        parts[8] = mark
                    lines[i] = '\t'.join(parts)
                    lines = find_conj(parts[0], lines, parts)
                    lines = mark_whole_clause(lines, lines[i], mark)

        elif len(parts) > 1 and parts[7] == 'parataxis' and '<' not in parts[1]:
            if find_nsubj(parts[0], lines) or parts[3] == 'VERB':
                mark = check_pos(parts, lines)
                if mark:
                    if parts[8] != '_':
                        parts[8] = parts[8] + '|' + mark
                    else:
                        parts[8] = mark
                    lines[i] = '\t'.join(parts)
                    lines = find_conj(parts[0], lines, parts)
                    lines = mark_whole_clause(lines, lines[i], mark)

        elif len(parts) > 1 and parts[7] == 'conj' and 'clause' not in parts[8]:
            num = parts[6]
            for line in lines:
                if line.split('\t')[0] == num:
                    root_line = line
            if check_conj(parts, root_line.split('\t'), lines):
                mark = check_pos(parts, lines)
                if mark:
                    if parts[8] != '_':
                        parts[8] = parts[8] + '|' + mark
                    else:
                        parts[8] = mark
                    lines[i] = '\t'.join(parts)
                    lines = find_conj(parts[0], lines, parts)
                    lines = mark_whole_clause(lines, lines[i], mark)

    new_sent = '\n'.join(lines)
    return new_sent


# Add has_dep
def find_fathers(sent):
    lines = sent.split('\n')
    fathers = []
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[3] != 'PUNCT':
            father = parts[6]
            fathers.append(father)
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if parts[0] in fathers:
            if parts[8] != '_':
                parts[8] = parts[8] + '|has_dep'
            else:
                parts[8] = 'has_dep'
            lines[i] = '\t'.join(parts)
            sent = '\n'.join(lines)
    return sent


# Замена для зависимостей, которые не требуют отдельных условий
def simple_replace(sent, mark, replace_mark):
    lines = sent.split('\n')
    for i in range(len(lines)):
        parts = lines[i].split('\t')
        if len(parts) > 1 and parts[7] == mark:
            if parts[8] == '_':
                parts[8] = replace_mark
            else:
                parts[8] = parts[8] + '|' + replace_mark
            lines[i] = '\t'.join(parts)
            lines = mark_whole_clause(lines, lines[i], replace_mark)
    sent = '\n'.join(lines)
    return sent


# Добавление всех типов помет
def mark_all(sents):
    for i in range(len(sents)):
        sents[i] = simple_replace(sents[i], 'root', 'clause_main')
        sents[i] = simple_replace(sents[i], 'acl:relcl', 'clause_subj')
        sents[i] = simple_replace(sents[i], 'ccomp', 'clause_subj')

        sents[i] = mark_acl(sents[i])
        sents[i] = mark_advcl(sents[i])
        sents[i] = mark_parataxis(sents[i])

        sents[i] = mark_clause_type(sents[i])
        sents[i] = find_fathers(sents[i])
    sents = mark_ellipsis(sents)
    return sents

