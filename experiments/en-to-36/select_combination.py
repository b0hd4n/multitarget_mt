#!/usr/bin/env python3
# ./select_combination.py N file_with_elements.txt 2-5,11
# from `file_with_elements.txt` which is \n separated list of elements
# select N-th combination and print to stdout

import sys
import itertools
import random

random.seed(1)

N = int(sys.argv[1])
data = sys.argv[2]
sizes = sys.argv[3]

# read languages
langs = []
with open(data) as f:
    for line in f:
        langs.append(line.strip())

# unfold combinations
combinations = []
for number in  sizes.split(','):
    if number.find('-') == -1:
        combinations.append(int(number))
    else:
        _from, _to = number.split('-')
        for comb in range(int(_from), int(_to)+1):
            combinations.append(comb)

# combinations generator
def combinations_generator(combinations, elements):
    while True:
        batch = []
        for c in combinations:
            batch.extend(itertools.combinations(elements, c))

        random.shuffle(batch)

        for combination in batch:
            yield ' '.join([str(x) for x in combination])

# select N-th
gen = combinations_generator(combinations, langs)
print(next(itertools.islice(gen, N, None)))

