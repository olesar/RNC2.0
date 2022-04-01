import json
from pymystem3 import Mystem
from pyasn1.compat.octets import null
from xml.etree import ElementTree


# Опции от Сергея Гладилина:   mystem_ruscorpora --format=json -i -c -g --eng-gr
# Также предлагается -w, если мы удовлетворительно работаем с незнакомыми словами
# Для полного набора опций надо брать pymystem из git: pip install git+https://github.com/nlpub/pymystem3 (см. https://github.com/nlpub/pymystem3).
m = Mystem(mystem_bin='./mystem_ruscorpora.linux', grammar_info=True, disambiguation=False, entire_input=True, glue_grammar_info=True, use_english_names=True)
# Вариант mystem с леммой несовершенного вида у глаголов совершенного вида
#masp = Mystem(grammar_info=True, disambiguation=False, entire_input=True, glue_grammar_info=True, use_english_names=True)


class MystemFixLists(object):
    def __init__(self):
        self.add_fix = self.load_add_cfg()
        self.del_fix = self.load_del_cfg()

    def load_add_cfg(self):
        result = {}
        with open('add.cfg', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line[0] == '+':
                    line = line[1:]
                tb = line.find(' ')
                token = line[0:tb]
                anas = '<root>' + line[tb+1:] + '</root>'
                root = ElementTree.fromstring(anas)
                if len(root.getchildren()) == 0:
                    continue
                result[token] = set()
                for child in root:
                    result[token].add( (child.attrib['lex'], child.attrib['gr']) )
        return result
    
    def load_del_cfg(self):
        result = {}
        with open('del.cfg', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 3:
                    print('del.cfg skip: '+line)
                    continue
                if parts[1].find('*') != -1:
                    print('del.cfg skip: '+line)
                    continue
                if parts[0][-1] == '*':
                    pattern = 'begins'
                    parts[0] = parts[0][:-1] 
                elif parts[0][0] == '*': 
                    pattern = 'ends'
                    parts[0] = parts[0][1:]
                else:
                    pattern = 'full'
                result[parts[1]] = (parts[2], pattern, parts[0])
        return result
    
    def get_pos_from_gr(self, g):
        g1 = g.replace('=', ',')
        p = g1.find(',')
        if p == -1:
            return ''
        else:
            return g[:p]
    
    def fix(self, variants, token):
        tfl = token.lower()
        if token in self.add_fix:
            variants.update(self.add_fix[token])
        removers = []
        for l, g in variants:
            if not l in self.del_fix:
                continue
            pos, pattern, text = self.del_fix[l]
            if self.get_pos_from_gr(g) != pos:
                continue
            if pattern == 'full' and tfl == text:
                removers.append((l,g))
            if pattern == 'begins' and tfl.startswith(text):
                removers.append((l,g))
            if pattern == 'ends' and tfl.endswith(text):
                removers.append((l,g))
        appends = []
        for l, g in variants:
            if self.get_pos_from_gr(g) == 'A' and g.find('|comp)') != -1 and tfl.endswith('щей') and l.endswith('щий'):
                removers.append((l,g))
                appends.append( (l,g.replace('|comp)',')')) )
        for r in removers:
            variants.remove(r)
        for a in appends:
            variants.update([a])
            #print(variants)
        
    
# объект для коррекции mystem-разборов специальными правилами (add.cfg, del.cfg)
fix_lists = MystemFixLists()


def get_variants(m, w):
    result = set()
    a = m.analyze(w)
    if not a:
        return result
    v = a[0]
    if not 'text' in v or v['text'] != w.lower(): # Можно ожидать, что mystem раздробит токен, что-то приклеит и т.п. Если это случилось, ничего не возвращаем.
        return result
    if not 'analysis' in v:
        return result
    for l in v['analysis']:
        if 'lex' in l and 'gr' in l:
            result.add( (l['lex'], l['gr']) )
    return result

def mystem_gr_to_sets(g):
    # замещение = на ,
    g1 = g.replace('=', ',')
    # если в конце строки запятая, удалим ее (чтобы не мешала split)
    if g1 and g1[-1] == ',':
        g1 = g1[:-1]
    # снимем скобки в которых нет альтернатив
    lp = g1.find('(')
    while lp != -1:
        rp = g1.find(')', lp+1)
        if rp == -1:  # нарушение скобочной стркутуры
            print('ERROR: invalid parenthesis:' + g1)
            break
        internal_str = g1[lp+1:rp]
        if internal_str.find('|') == -1:
            g1 = g1[:lp] + g1[lp+1:rp] + g1[rp+1:]
            lp = g1.find('(', rp-1)
        else:
            lp = g1.find('(', rp+1)
    # удостоверимся, что остался лишь один блок с альтернативами
    pcnt = g1.count('(')
    if pcnt > 1:
        #print('ERROR: anomaly gr: ' + g1)
        return set('ANOMALY'), None
    # обрабатываем случай, когда альтернатив нет
    if pcnt == 0:
        g_gr_set = set(g1.split(','))
        return g_gr_set, None 
    # особая обработка альтернативных групп в скобках
    if pcnt == 1:
        lp = g1.find('(')
        rp = g1.find(')', lp+1)
        alt_block = g1[lp+1:rp]
        g1 = g1[:lp] + g1[rp+1:]
        g1 = g1.replace(',,', ',')
#         if not g1:
#             print(g)
        if g1 and g1[-1] == ',':
            g1 = g1[:-1]
        g_gr_set = set(g1.split(','))
        alt_gr_set = set(alt_block.split('|'))
        return g_gr_set, alt_gr_set

def exclude_qbic(variants, info_lex, info_gr):
    info_gr_set = set(info_gr.replace('=', ',').split(','))
    removers, replacers = [], []
    for l, g in variants:
        if l != info_lex:
            continue
#         if g == '(CONJ|PART)':
#             print('(CONJ|PART)')
#             print(variants)
#             print(info_lex)
#             print(info_gr)
        g_gr_set, alt_gr_set = mystem_gr_to_sets(g)
        if not alt_gr_set:
            # обрабатываем случай, когда альтернатив нет
            # если mystem ничего нового не добавляет, то это лишний вариант (qbic полностью его покрыл и может добавил еще что-то)
            diff = g_gr_set.difference(info_gr_set)
            if not diff:
                removers.append((l,g))
                continue
        else:
            # особая обработка альтернативных групп в скобках
            to_del_list = []
            for a in alt_gr_set:
                a1 = set(a.split(','))
                u = g_gr_set.union(a1)
                diff = u.difference(info_gr_set)
                if not diff:
                    to_del_list.append(a)
            if len(to_del_list) == len(alt_gr_set):  # все альтернативы подлежат удалению
                removers.append((l,g))
                continue
            elif to_del_list:
                for to_del in to_del_list:
                    pos = g.find(to_del)
                    g2 = g[:pos] + g[pos+len(to_del):]
                    if g2[pos] == '|':
                        g2 = g2[:pos] + g2[pos+1:]
                    elif g2[pos] == ')':
                        g2 = g2[:pos-1] + g2[pos:]
                    else:
                        print('ERROR: alt struct: ' + g + ', to_del=' + to_del)
                        return
                removers.append((l,g))
                replacers.append((l,g2))
            
    # удаляем разборы, уже имеющиеся у qbic        
    for r in removers:
        variants.remove(r)
    # добавляем скорректированные (по альтернативам)
    for r in replacers:
        variants.add(r)
        

def exclude_qbic_multi(variants, info):
    if len(info['lex']) != len(info['gr']):
        return
    for i in range(len(info['lex'])):
        exclude_qbic(variants, info['lex'][i], info['gr'][i])

# def append_imperfect_lemma_multi(variants, info):
#     result = set()
#     if len(info['lex']) != len(info['gr']):
#         return result
#     for info_gr, info_lex in zip(info['gr'], info['lex']):
#         info_gr_set = set(info_gr.replace('=', ',').split(','))
#         if not 'V' in info_gr_set or not 'pf' in info_gr_set:
#             continue
#         # если среди qbic-разборов есть глагольная форма совершенного вида, то поищем аналог с леммой несовершенного вида
#         for l, g in variants:
#             g_gr_set, alt_gr_set = mystem_gr_to_sets(g)
#             if not 'V' in g_gr_set or l == info_lex:
#                 continue
#             if 'pf' in g_gr_set:
#                 result.add( l )
#             elif alt_gr_set:
#                 for a in alt_gr_set:
#                     a1 = a.split(',')
#                     if 'pf' in a1:
#                         result.add( l )
#                         break
#     return result

def extend_by_mystem(info):
    variants = get_variants(m, info['token'])
    fix_lists.fix(variants, info['token'])
    exclude_qbic_multi(variants, info)
    v = sorted(variants)
#     vasp = get_variants(masp, info['token'])
#     fix_lists.fix(vasp, info['token'])
#     v2 = append_imperfect_lemma_multi(vasp, info)
    f_ana = '<anam lex="{}" gr="{}"/>'
    result = ''
    for l, g in v:
        result += f_ana.format(l, g)
#     f_ana2 = '<anam lex_ipf ="{}"/>'
#     for l in v2:
#         result += f_ana2.format(l)
    return result
