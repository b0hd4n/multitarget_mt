#!/usr/bin/env python3

import argparse
import random
import itertools
import sys
from collections import defaultdict, deque


def main():
    args = parse_args()
    random.seed(args.seed)
    elements = read_elements(args)
    combinations = []
    for comb_size in args.sizes:
        combinations.extend(get_combinations(elements, comb_size, args.min_count))

    random.shuffle(combinations)

    for combination in combinations:
        print(" ".join(list(combination)))


def cs_range(value):
    result = []
    for number in value.split(','):
        if number.find('-') == -1:
            result.append(int(number))
        else:
            _from, _to = number.split('-')
            _from, _to = int(_from), int(_to)
            if _from >= _to:
                raise ValueError('Invalid subrange: {}'.format(number))
            for comb in range(_from, _to+1):
                result.append(comb)
    result = sorted(list(set(result)))
    return result


def parse_args():
    parser = argparse.ArgumentParser(description='Generate combinations with min. level of presence of each element')

    parser.add_argument(
        '--seed',
        type=int,
        default=1,
        help='Seed for randomizer',
    )

    parser.add_argument(
        '--min_count',
        type=int,
        default=1,
        help='Each element is presented min_count times (default 1)',
    )

    parser.add_argument(
        '--filename',
        type=str,
        default=None,
        help='File with elements; each element in one line. If none - reads from stdin.',
    )

    parser.add_argument(
        '--sizes',
        type=cs_range,
        help='Sizes of combinations. 2,4-6,8 is 2,4,5,6,8',
    )

    return parser.parse_args()
    

def read_elements(args):
    result = []
    if args.filename is not None:
        with open(args.filename) as f:
            for line in f:
                result.append(line.strip())
    else:
        for line in sys.stdin:
            result.append(line.strip())

    return result


def get_combinations(elements, comb_size, min_count):
    counts = defaultdict(int)
    N = len(elements)
    combinations = list(itertools.combinations(elements, comb_size))
    random.shuffle(combinations)
    result = []
    for combination in combinations:
        if any([counts[lang] < min_count for lang in combination]):
            result.append(combination)
            for lang in combination:
                counts[lang] += 1

            if N is not None and len(counts) < N:
                continue

            if all(v >= min_count for v in counts.values()):
                break
    return result


def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return itertools.zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)

def get_ballanced_combinations(elements, comb_size, min_count):
    result = []
    els = elements.copy()
    random.shuffle(els)
    els = deque(els)
    tail_len = comb_size - len(els) % comb_size
    for i in range(min_count):
        # perform shift
        els.rotate(1)
        result.extend(list(grouper(comb_size,list(els)+list(els)[:tail_len],None)))
    return result

if __name__=='__main__':
    main()
