#!/usr/bin/env python3 

import argparse
import os
import sys

def main():
    args = parse_args()
    fix_train_log(args)
    
def parse_args():
    parser = argparse.ArgumentParser(description='Fix for older train logs that did not contain intividual BLEU scores')
    parser.add_argument(
        '--experiment-dir', '-d',
        type=str,
        help='Folder with experiment',
    )

    args = parser.parse_args()
    return args

def fix_train_log(args):
    full_path = lambda x: os.path.join(args.experiment_dir, x)
    with open(full_path('valid.log'), encoding='utf-8') as valid,\
         open(full_path('train.log'), encoding='utf-8') as train,\
         open(full_path('fixed_train.log'), 'w', encoding='utf-8') as fixed_train:
        # find valid/translation, append lang/bleu_xx
        train_lines = (line for line in train)
        for step, valid_portion in generate_valid_portion(valid):
            for line in train_lines:
                line = line.strip()
                current_step = get_step(line)
                if current_step is None:
                    print(line, file=fixed_train)
                    continue
                if current_step == step:
                    valid_portion.discard(line)
                if current_step > step:
                    for leftover_line in valid_portion:
                        print(leftover_line, file=fixed_train)
                    print(line, file=fixed_train)
                    break
                print(line, file=fixed_train)

    print('done')


def generate_valid_portion(valid_file):
    """
    Yields set of valid.log lines with the same step (Up. xx)
    """
    valid_lines = (line for line in valid_file)
    first_line = valid_lines.__next__()
    step = get_step(first_line)
    accumulator = set([first_line])

    for line in valid_lines:
        line = line.strip()
        current_step = get_step(line)
        if current_step != step:
            yield step, accumulator
            step = current_step
            accumulator = set()

        accumulator.add(line)

    yield step, accumulator
    yield sys.maxsize, set()


def get_step(line):
    """
    Returns step (Up. xxx) if line contains it
    """
    if 'Up.' not in line:
        return None
    update = int(line.split('Up.')[1].strip().split(' ')[0])
    #print(line, update, 'update')
    return update


if __name__ == '__main__':
    main()
