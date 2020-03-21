#!/usr/bin/env python3
# filter out lines specified in another file

import sys
import argparse

def main():
    args = parse_args()
    skipped_lines_generator = get_skipped_line_generator(args.lines)
    with open(args.source, encoding='utf-8') as f_data:
        skip_line = next(skipped_lines_generator)
        for i, data_line in enumerate(f_data, 1):
            if i == skip_line:
                skip_line = next(skipped_lines_generator)
            else:
                print(data_line.strip())

def parse_args():
    parser = argparse.ArgumentParser(description='Filter out lines specified in another file.')
    parser.add_argument('--lines', '-l', type=str,
                        help='File contains lines to skip')
    parser.add_argument('--source', '-s', type=str,
                        help='Source file to be filtered')

    args = parser.parse_args()
    return args

def get_skipped_line_generator(lines_file):
    with open(lines_file) as f:
        for line in f:
            yield int(line)
    yield -1

if __name__=='__main__':
    main()
