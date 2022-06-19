import re
import argparse
import sys
import os
from tqdm import tqdm


def do_single(file_path, out_file_path):
    if (os.path.splitext(file_path)[-1] != '.conllu'):
        return
    os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
    with open(file_path, 'r', encoding="utf-8") as infile, open(out_file_path, 'w',
                                                             encoding='utf-8', newline='\n') as outfile:
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
            for header_line in header:
                outfile.write(header_line + '\n')
            counter = 1
            for body_line in body:
                outfile.write(str(counter) + '\t' + "\t".join(body_line[1:]) + '\n')
                counter += 1
            outfile.write('\n')


def do_multiple(root_folder, result_folder_path):
    walk = [(x, y, z) for x, y, z in os.walk(root_folder)]
    dir_len = 0
    for root, dirs, files in walk:
        for file in files:
            dir_len += 1
    pbar = tqdm(total=dir_len)
    for root, dirs, files in walk:
        for file in range(len(files)):
            new_file_path = os.path.join(result_folder_path + root.replace(root_folder, ""), files[file])
            f_path = os.path.join(root, files[file])
            do_single(f_path, new_file_path)
            pbar.update()
    pbar.close()


def main():
    parser = argparse.ArgumentParser(description='fixing numeration')
    parser.add_argument('single_or_folder', type=str, help='if file is single or folder')
    parser.add_argument('source_path', type=str, help='source_path')
    parser.add_argument('result_path', type=str, help='result_path')
    args = parser.parse_args()

    if len(sys.argv) != 4:
        sys.exit(-1)

    if args.single_or_folder == 'single':
        do_single(args.source_path, args.result_path)
    elif args.single_or_folder == 'folder':
        do_multiple(args.source_path, args.result_path)
    else:
        print('fix_numbers.py <single/folder> <filepath/root_dir> <output_path/output_dir>')
        print('example for single file: fix_numbers.py single test_file.conllu result_file.conllu')
        print('example for folder: fix_numbers.py folder test_folder result_folder')


if __name__ == '__main__':
    main()
