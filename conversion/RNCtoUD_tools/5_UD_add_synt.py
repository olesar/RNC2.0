# from ufal.udpipe import Model, Pipeline, ProcessingError
#
# m = Model.load("GE20_STR-v2.udpipe")
# pipeline = Pipeline(m, 'conllu', Pipeline.NONE, Pipeline.DEFAULT, 'conllu')
# error = ProcessingError()


def parse_text(text, pipeline, error):
    text = text.replace(' ', '\\s')
    parsed_text = pipeline.process(text, error)
    if error.occurred():
        print('Error:', error.message)
    parsed_text = parsed_text.replace('\\s', ' ')
    return parsed_text


# with open('marx_basic_ud.conllu', 'r', encoding='utf-8') as f:
#     text = f.read()
# with open('test_files_RNC_basicSynt/marx_basicUD.conllu', 'w', encoding='utf-8') as f:
#     f.write(parsed_text)
