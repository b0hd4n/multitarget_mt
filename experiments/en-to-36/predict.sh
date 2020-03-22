#!/bin/bash

#MARIAN=../tools/marian
if [ ! $MARIAN ];
then
	echo MARIAN variable is not set
	exit 1;
fi

if [ $# -ne 2 ]
then
    echo "model_name target_lang"
    exit 1
fi

MODEL_NAME=$1
TARGET_LANG=$2

SOURCE=data/interim/en2${TARGET_LANG}.val.source.gz
GOLD=data/interim/en2${TARGET_LANG}.val.target.gz
OUTPUT=data/interim/${MODEL_NAME}_${TARGET_LANG}.output

# translate dev set
cat $SOURCE \
    | $MARIAN/build/marian-decoder -c model_en2${MODEL_NAME}/model.npz.decoder.yml -d 0 1 -b 6 -n0.6 \
    --vocabs data/interim/vocab.en.spm data/interim/vocab.${MODEL_NAME}.spm \
    --mini-batch 64 --maxi-batch 100 --maxi-batch-sort src \
      > $OUTPUT

cat $OUTPUT \
    | moses-scripts/scripts/generic/multi-bleu-detok.perl $GOLD 
    #| sed -r 's/BLEU = ([0-9.]+),.*/\1/'
