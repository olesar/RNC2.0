import os
from ufal.udpipe import Model, Pipeline, ProcessingError
xml_fix_punctuation = __import__('1_xml_fix_punctuation')
RNC_to_UD_ext = __import__('2_RNC_to_UD-ext(tags_format)')
split_sentences = __import__('3_UD-ext_split_sentences')
join_sentences = __import__('3(1)_UD-ext_join_sentences')
UD_ext_to_base = __import__('4_UD_ext_to_UD_base')
UD_add_synt = __import__('5_UD_add_synt')
UD_back_to_ext = __import__('6_UDsynt_to_UDsynt_ext')


def get_RNCtoUD_table(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        tags_table = f.read()
    tags = tags_table.split('\n')
    tags_dict = {}
    for tag in tags:
        if tag != '':
            parts = tag.split('\t')
            tags_dict[parts[0]] = parts[1]
    return tags_dict


def get_list_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    some_list = text.split('\n')
    return some_list


tags_dict = get_RNCtoUD_table('data_lists/RNCtoUDtable-ext.txt')
cconj_list = get_list_from_file('data_lists/CCONJ_list.txt')
sym_list = get_list_from_file('data_lists/symbols_with_xml.txt')
m = Model.load("GE20_STR-v2.udpipe")
pipeline = Pipeline(m, 'conllu', Pipeline.NONE, Pipeline.DEFAULT, 'conllu')
error = ProcessingError()

filepath = 'test_files_RNC\\marx.xml'
output_path = 'test_result_UD\\marx.conllu'


def RNC_to_UD(f_path, output_path):
    with open(f_path, 'r', encoding='utf-8') as f:
        text = f.read()
    text_fixed = xml_fix_punctuation.fix_punctuation(text)
    conllu_text = RNC_to_UD_ext.RNCtoUD_one_text(text_fixed, sym_list, cconj_list, tags_dict)
    conllu_text = split_sentences.split_text_sents(conllu_text)
    conllu_text = join_sentences.join_text_sents(conllu_text)
    basic_conllu_text = UD_ext_to_base.convert_to_basic(conllu_text)
    conllu_with_synt = UD_add_synt.parse_text(basic_conllu_text, pipeline, error)
    ext_conllu_with_synt = UD_back_to_ext.basic_to_ext(conllu_with_synt, conllu_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ext_conllu_with_synt)

RNC_to_UD(filepath, output_path)

# for all files in directory:

# root_dir = 'some_directory'
# walk = [(x, y, z) for x, y, z in os.walk(root_dir)]
# for root, dirs, files in walk:
#     for f in files:
#         f_path = os.path.join(root, f)
#         conllu_name = '.'.join(f_path.split('.')[:-1]) + '.conllu'
#         file_output_path = output_path + conllu_name
#         os.makedirs(os.path.dirname(file_output_path), exist_ok=True)
#         RNC_to_UD(f_path, file_output_path)
