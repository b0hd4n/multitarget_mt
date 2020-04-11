#!/usr/bin/env bash

cd `dirname $0`

MODEL_FOLDER=$(basename $(pwd))
langs=($(echo $MODEL_FOLDER | sed 's/model_en2\(.*\)/\1/g' | sed 's/\(..\)/\1 /g'))

translations=$(basename $1)

# find last line from train log that contains epoch and update number
# and reuse it when constructing the line with bleu score

LAST_TRAIN_LOG_LINE=$(awk '/Ep./{k=$0}END{print k}' train.log )
update=$(echo $LAST_TRAIN_LOG_LINE | sed 's/.* Up. \([0-9]*\) :.*/\1/')
epoch=$(echo $LAST_TRAIN_LOG_LINE | sed 's/.* Ep. \([0-9]*\) :.*/\1/')

# find the latest step and epoch in training log

for lang in ${langs[@]};
do
    gold_file=$(mktemp)
    pred_file=$(mktemp)

    TLANG_REGEX="<2\\(${lang}\\)>"
    paste val.source $translations \
                                | grep -e $TLANG_REGEX \
                                | cut -f2 \
                                | tgt=$lang ../postprocess.sh \
        > $pred_file
    paste val.source val.target \
                                | grep -e $TLANG_REGEX \
                                | cut -f2 \
                                | tgt=$lang ../postprocess.sh \
        > $gold_file


    result=$(cat $pred_file | ../sacreBLEU/sacrebleu.py --score-only $gold_file)
    results="${results} ${result}"

    rm $pred_file
    rm $gold_file

    current_output= date +"[%Y-%m-%d %T]"
    current_output= "$current_output [valid] Ep. ${epoch} : Up. ${update} :"
    current_output= "$current_output lang/bleu-${lang} : ${result} :"
    current_output= "$current_output no effect on early stopping"

    echo $current_output >> valid.log
    echo $current_output >> train.log
done

#####################################
# Now compute average and report it #

results=($results)
function join_by { local IFS="$1"; shift; echo "$*"; }

#print geom.avg
python3 -c "import math; print(math.pow($(join_by \* ${results[@]}), 1. / ${#results[@]} )) "
