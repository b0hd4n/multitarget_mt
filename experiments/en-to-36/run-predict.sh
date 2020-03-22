#!/bin/bash

if [ $# -ne 2 ]
then
    echo "model_name target_lang"
    exit 1
fi

MODEL_NAME=$1
TARGET_LANG=$2

qsub -N "m.${MODEL_NAME}_t.${TARGET_LANG}" -m n -j y -b y -cwd -q gpu* \
    -l gpu=2,gpu_ram=8G,mem_free=50G,act_mem_free=50G,h_data=50G \
    ./predict.sh ${MODEL_NAME} ${TARGET_LANG}
