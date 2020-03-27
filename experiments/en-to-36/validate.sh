#!/usr/bin/env bash

cd `dirname $0`

MODEL_FOLDER=$(basename $(pwd))
langs=($(echo $MODEL_FOLDER | sed 's/model_en2\(.*\)/\1/g' | sed 's/\(..\)/\1 /g'))

translations=$(basename $1)

# WARNING!
# let's hope another metrics are already in valid.log
valid_log_template=$(tail -1 valid.log | cut -d' ' -f -9)

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

    # WARNING! hack
    # I hope at this point previous val scores are allready in valid.log
    # so let's just past these numbers there also
    # it won't be visible for the validation early stopping, but will be for tensorboard
    echo $valid_log_template lang/bleu-${lang} : ${result} : no effect on early stopping >> valid.log
    echo $valid_log_template lang/bleu-${lang} : ${result} : no effect on early stopping >> train.log
done

#####################################
# Now compute average and report it #

results=($results)
function join_by { local IFS="$1"; shift; echo "$*"; }

#print geom.avg
python3 -c "import math; print(math.pow($(join_by \* ${results[@]}), 1. / ${#results[@]} )) "
