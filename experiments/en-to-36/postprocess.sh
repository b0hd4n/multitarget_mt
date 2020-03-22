#!/usr/bin/env bash

cd `dirname $0`
#echo $(pwd)
[[ -z "$NUM_THREADS" ]] && NUM_THREADS=1

sed -r 's/\@\@ //g' | \
  moses-scripts/scripts/recaser/detruecase.perl 2>/dev/null | \
  moses-scripts/scripts/tokenizer/detokenizer.perl -threads $NUM_THREADS -lines 10000 -l $tgt 2>/dev/null
