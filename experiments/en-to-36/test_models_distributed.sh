#!/usr/bin/env bash

# 1. find out what model to evaluate; which languages
# 2. run server with this model
# 3. iterate over langs
# 4. evaluate for each dataset for selected lang
# 5. write to  RESULT_DIR/results.tsv each result
# 6. add model to RESULT_DIR/evaluated_models


# 1. find out what model to evaluate; which languages
MODEL=$(sed "${SGE_TASK_ID}q;d" ${MODELS_LIST})
langs=($(echo $MODEL | sed 's/model_en2\(.*\)/\1/g' | sed 's/\(..\)/\1 /g'))
[[ -z "$RESULT_DIR" ]] && RESULT_DIR=test_results
# different ports - tasks may be on the same cluster
PORT=$(("$SGE_TASK_ID" + 8080))

# for client script
source ./test_env/bin/activate

# 2. run server with this model
for decoder in $(ls ${MODEL}/*decoder.yml | grep 'best')
do
    # don't forget to kill server afterwards
    nohup $MARIAN/build/marian-server --port $PORT -c $decoder --mini-batch 64 --maxi-batch 100 --maxi-batch-sort src -w 9000 &>/dev/null &
    SERVER_PID=$!
    sleep 15
    trap "echo stopping marian server; kill $SERVER_PID" EXIT
    echo $SERVER_PID server pid
    echo $PORT port
    ps -p $SERVER_PID -o comm=
    BEST_BY=$(echo $decoder | cut -d '.' -f 3 | cut -d'-' -f 2- )
# 3. iterate over langs
    for TARGET_LANG in ${langs[@]}
    do
# 4. evaluate for each dataset for selected lang
        for dataset in $(find data/raw/test/en2${TARGET_LANG} -maxdepth 2 -mindepth 2 -type d)
        do
            DATASET_NAME=$(echo $dataset | cut -d'/' -f 5-) 
            #get bleu
            BLEU=$( cat $dataset/*.bpe.en | $MARIAN/scripts/server/client_example.py -p $PORT   \
                         | tgt=$TARGET_LANG ./postprocess.sh \
                         | ./sacreBLEU/sacrebleu.py --score-only $dataset/*en2$TARGET_LANG.$TARGET_LANG )
# 5. write to  RESULT_DIR/results.tsv each result
            printf "%s\t%s\t%s\t%s\t%.2f\n" $MODEL $TARGET_LANG $BEST_BY $dataset $BLEU >> ${RESULT_DIR}/results.tsv
            printf "%s\t%s\t%s\t%s\t%.2f\n" $MODEL $TARGET_LANG $BEST_BY $dataset $BLEU 
        done
    done
    
# 6. add model to RESULT_DIR/evaluated_models
    echo $MODEL >> ${RESULT_DIR}/evaluated_models
    # kill marian server with the decoder
    kill $SERVER_PID
done