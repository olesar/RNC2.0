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


# with open('test_files_RNC_basicSynt\\marx_basicUD.conllu', 'r', encoding='utf-8') as f:
#     basic_synt_text = f.read()
# sentences = basic_synt_text.split('\n\n')[:-1]
# with open('marx_split_result.conllu', 'r', encoding='utf-8') as f:
#     ext_text = f.read()
# ext_sentences = ext_text.split('\n\n')[:-1]

# with open('test_files_RNC_basicSynt\\marx_extUD.conllu', 'w', encoding='utf-8') as f:
#     f.write(ext_synt_text)
    