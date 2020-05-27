#!/usr/bin/env python3

import sys
from collections import defaultdict, Counter

source_filename = sys.argv[1]
target_filename = sys.argv[2]
languages = \
        ['ar', 'az', 'bg', 'bs', 'cs', 'da', 'de', 'el', 'es', 'et', 'fi', 'fr', 
         'ga', 'he', 'hr', 'hu', 'is', 'it', 'ka', 'lt', 'lv', 'mk', 'mt', 'nl', 
         'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'tr', 'uk', ]

sentences_count = defaultdict(int)
src_subwords_count = defaultdict(int)
tgt_subwords_count = defaultdict(int)

source_subwords = defaultdict(Counter)
target_subwords = defaultdict(Counter)

with open(source_filename, encoding='utf-8') as source, \
     open(target_filename, encoding='utf-8') as target:
    for line, (src_line, tgt_line) in enumerate(zip(source, target)):
        # <2ln> source sentence
        # target sentence
        src_tokens = src_line.strip().split()
        tgt_tokens = tgt_line.strip().split()
        
        # <2ln> -> ln
        tgt_lang = src_tokens[0][2:-1]
        src_tokens = src_tokens[1:]

        sentences_count[tgt_lang] += 1
        src_subwords_count[tgt_lang] += len(src_tokens)
        tgt_subwords_count[tgt_lang] += len(tgt_tokens)

        source_subwords[tgt_lang].update(src_tokens)
        target_subwords[tgt_lang].update(tgt_tokens)

        if line % 10000 == 0:
            print('.', end='', flush=True)
        if line % 1000000 == 0:
            print(line)
            print('sentences_count', sentences_count)
            print('src_subwords_count ', src_subwords_count)
            print('tgt_subwords_count ', tgt_subwords_count)
            print()

languages = list(sentences_count.keys())

for lang in languages:
    try:
        with open(f'{lang}.src.subwords', 'w', encoding='utf-8') as src:
            for subword, count in source_subwords[lang].most_common():
                src.write(f'{count}\t{subword}\n')
        with open(f'{lang}.tgt.subwords', 'w', encoding='utf-8') as tgt:
            for subword, count in target_subwords[lang].most_common():
                tgt.write(f'{count}\t{subword}\n')
    except:
        print(f'no data for {lang}')
        continue

avg_src_len = {
    lang:src_subwords_count[lang] / sentences_count.get(lang,1)
    for lang in languages
}

avg_tgt_len = {
    lang:tgt_subwords_count[lang] / sentences_count.get(lang,1)
    for lang in languages
}

with open('statistics.csv', 'w', encoding='utf-8') as f:
    # csv header
    f.write('target_lang,sentences_count,avg_subwords_src,avg_subwords_tgt,total_subwords_src,total_subwords_tgt\n')
    for lang in languages:
        f.write(f'{lang},')
        f.write(f'{sentences_count.get(lang, "")},')
        f.write(f'{avg_src_len.get(lang, "")},')
        f.write(f'{avg_tgt_len.get(lang, "")},')
        f.write(f'{len(source_subwords[lang])},')
        f.write(f'{len(target_subwords[lang])}\n')

print('Done')
