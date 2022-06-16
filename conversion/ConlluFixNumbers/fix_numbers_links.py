import re
import argparse
import sys
import os


def main():
    parser = argparse.ArgumentParser(description='fixing numeration')
    parser.add_argument('folder_path', type=str, help='folder path')
    parser.add_argument('new_folder_path', type=str, help='new folder path')
    args = parser.parse_args()

    if len(sys.argv) != 3:
        print('fix_numbers.py  <folder_path> <new_folder_path>')
        sys.exit(-1)

    folder_path = args.folder_path
    new_folder_path = args.new_folder_path

    for path, subdirs, files in os.walk(folder_path):
        for name in files:
            file_path = os.path.join(path, name)
            new_file_path = new_folder_path + "/" + "/".join(file_path.split("/")[5:])

            new_file_subfolder_path = "/".join(new_file_path.split("/")[:-1])
            print(new_file_subfolder_path)

            if not os.path.exists(new_file_subfolder_path):
                os.makedirs(new_file_subfolder_path)

            with open(file_path, 'r', encoding="utf-8") as infile, open(new_file_path, 'w',
                                                                        encoding='utf-8') as outfile:
                file_text_list = infile.read().strip('\n').split('\n\n')
                for paragraph in file_text_list:
                    header = []
                    body = []
                    paragraph_text = paragraph.split('\n')
                    if paragraph_text[0] != "":
                        for line in paragraph_text:
                            # print(line)
                            if len(line) > 0:
                                if re.search('[0-9]', line[0]):
                                    body.append(line.strip('\n').split('\t'))
                                else:
                                    header.append(line.strip('\n'))
                    # print('header', '\n', header)
                    # print('body', '\n', body)
                    for header_line in header:
                        outfile.write(header_line + '\n')
                    fixed_body = []
                    for body_line in body:
                        if body_line[6] != '':
                            link = body_line[6]
                            # print(link)
                            found = False
                            for index in range(len(body)):
                                if body[index][0] == link:
                                    new_body_line_list = []
                                    new_body_line_list.extend(body_line[1:6])
                                    new_body_line_list.append(str(index + 1))
                                    new_body_line_list.extend(body_line[7:])
                                    # print(new_body_line_list)
                                    fixed_body.append(new_body_line_list)
                                    found = True
                                    break
                            if not found:
                                if int(link) == 0:
                                    fixed_body.append(body_line[1:])
                                else:
                                    new_body_line_list = []
                                    new_body_line_list.extend(body_line[1:6])
                                    new_body_line_list.append('1')
                                    new_body_line_list.extend(body_line[7:])
                                    # print(new_body_line_list)
                                    fixed_body.append(new_body_line_list)
                    counter = 1
                    for fixed_body_line in fixed_body:
                        # print(fixed_body_line)
                        outfile.write(str(counter) + '\t' + "\t".join(fixed_body_line) + '\n')
                        counter += 1
                    outfile.write('\n')


def fix_test_windows():
    file_path = 'test/n_chuk06.conllu'
    new_file_path = 'new_folder/n_chuk06.conllu'
    with open(file_path, 'r', encoding="utf-8") as infile, open(new_file_path, 'w', encoding='utf-8') as outfile:
        file_text_list = infile.read().strip('\n').split('\n\n')
        for paragraph in file_text_list:
            header = []
            body = []
            paragraph_text = paragraph.split('\n')
            if paragraph_text[0] != "":
                for line in paragraph_text:
                    # print(line)
                    if len(line) > 0:
                        if re.search('[0-9]', line[0]):
                            body.append(line.strip('\n').split('\t'))
                        else:
                            header.append(line.strip('\n'))
            # print('header', '\n', header)
            # print('body', '\n', body)
            for header_line in header:
                outfile.write(header_line + '\n')
            fixed_body = []
            for body_line in body:
                if body_line[6] != '':
                    link = body_line[6]
                    # print(link)
                    found = False
                    for index in range(len(body)):
                        if body[index][0] == link:
                            new_body_line_list = []
                            new_body_line_list.extend(body_line[1:6])
                            new_body_line_list.append(str(index + 1))
                            new_body_line_list.extend(body_line[7:])
                            # print(new_body_line_list)
                            fixed_body.append(new_body_line_list)
                            found = True
                            break
                    if not found:
                        if int(link) == 0:
                            fixed_body.append(body_line[1:])
                        else:
                            new_body_line_list = []
                            new_body_line_list.extend(body_line[1:6])
                            new_body_line_list.append('1')
                            new_body_line_list.extend(body_line[7:])
                            # print(new_body_line_list)
                            fixed_body.append(new_body_line_list)
            counter = 1
            for fixed_body_line in fixed_body:
                # print(fixed_body_line)
                outfile.write(str(counter) + '\t' + "\t".join(fixed_body_line) + '\n')
                counter += 1
            outfile.write('\n')


if __name__ == '__main__':
    # fix_test_windows()
    main()
