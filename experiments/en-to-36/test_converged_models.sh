#!/usr/bin/env bash

# set FILTER variable to filter models to be tested
#mkdir -p tmp
## not deleted: warning!
#MODELS=$(mktemp -p ./tmp)
#echo $MODELS
#chmod +wr ${MODELS}

[[ -z "$RESULT_DIR" ]] && RESULT_DIR=test_results
[[ -z "$CONC_TASKS" ]] && CONC_TASKS=1
[[ -z "$NEG_FILTER" ]] && NEG_FILTER='ar'

mkdir -p ${RESULT_DIR}
if [[ -z "$MODELS" ]]
then
    MODELS="${RESULT_DIR}/models_to_check"
    ./converged_models.sh | cut -d' ' -f 1 | grep "${FILTER}"  > $MODELS
else
    cp "$MODELS" "${RESULT_DIR}/models_to_check"
    MODELS="${RESULT_DIR}/models_to_check"
fi


jobs=$(cat $MODELS | wc -l )
echo $jobs

echo ${MODELS}

mkdir -p test_logs
qsub -N aj_test_models -m n -j y -b y -cwd -q gpu-*.q \
    -l gpu=1,gpu_ram=11G,mem_free=25G,act_mem_free=25G,h_data=25G \
    -pe smp 1 \
    -t 1-$jobs \
    -p -200 \
    -o 'test_logs/$JOB_NAME.$JOB_ID.$TASK_ID' \
    -v RESULT_DIR="${RESULT_DIR}" \
    -v MODELS_LIST="${MODELS}" \
    -tc $CONC_TASKS \
    ./test_models_distributed.sh
