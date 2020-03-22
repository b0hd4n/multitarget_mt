#!/usr/bin/env python3

import sys
from collections import defaultdict

min_count = int(sys.argv[1])
try:
    N = int(sys.argv[2])
except:
    N = None

combinations = []
counts = defaultdict(int)

for line in sys.stdin:
    line = line.strip()
    combination = line.split(' ')
    if any([counts[lang] < min_count for lang in combination]):
        print(line)
        combinations.append(combination)
        for lang in combination:
            counts[lang] += 1

        if N is not None and len(counts) < N:
            continue

        if all(v >= min_count for v in counts.values()):
            break

