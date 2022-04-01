from ufal.udpipe import Model, Pipeline, ProcessingError
import os

m = Model.load("GE20_STR-v2.udpipe")
pipeline = Pipeline(m, 'conllu', Pipeline.NONE, Pipeline.DEFAULT, 'conllu')
error = ProcessingError()


def parse_text(text, pipeline, error):
    text = text.replace(' ', '\\s')
    parsed_text = pipeline.process(text, error)
    if error.occurred():
        print('Error:', error.message)
    parsed_text = parsed_text.replace('\\s', ' ')
    return parsed_text


def basic_to_ext(basic_synt_text, ext_text):
    sentences = basic_synt_text.split('\n\n')[:-1]
    ext_sentences = ext_text.split('\n\n')[:-1]
    new_sents = []
    for i in range(len(sentences)):
        lines = sentences[i].split('\n')
        ext_lines = ext_sentences[i].split('\n')
        new_lines = []
        for j in range(len(lines)):
            if lines[j][0] == '#':
                new_lines.append(lines[j])
                continue
            parts = lines[j].split('\t')
            ext_parts = ext_lines[j].split('\t')
            if parts[3] != ext_parts[3]:
                parts[3] = ext_parts[3]
            if parts[5] != ext_parts[5]:
                parts[5] = ext_parts[5]
            new_lines.append('\t'.join(parts))
        new_sents.append('\n'.join(new_lines))
    ext_synt_text = '\n\n'.join(new_sents) + '\n\n'
    return ext_synt_text


# files = os.listdir('C:\\Users\\Yana\\project\\corpus_slice_conllu_basic')
# for f_name in files:
#     path = 'C:\\Users\\Yana\\project\\corpus_slice_conllu_basic\\' + f_name
#     print(f_name)
#     with open(path, 'r', encoding='utf-8') as f:
#         text = f.read()
#     parsed = parse_text(text, pipeline, error)
#     ext_path = 'C:\\Users\\Yana\\project\\corpus_slice_conllu\\' + f_name
#     with open(ext_path, 'r', encoding='utf-8') as f:
#         ext_text = f.read()
#     new_text = basic_to_ext(parsed, ext_text)
#     output_path = 'C:\\Users\\Yana\\project\\corpus_slice_conllu_synt\\' + f_name
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(new_text)
