#!/usr/bin/env bash

# If run directly:
# ./run-experiment fr
# for en2fr model
#
# ./run-experiment es cs
# for en2cses model
#
# If $SGE_TASK_ID is available (is sub-job of array job)
#
# SGE_TASK_ID=123 ./run-experiment.sh setups_list.txt
# each line of the file is space separated list of languages
#
# SGE_TASK_ID=123 ./run-experiment.sh select_langs.py
# >> select_langs.py 123
# "es fr ar"
# script returns space separated list of languages

source ./utils.sh

if [ ! $SOURCE_LANG ];
then
	SOURCE_LANG=en;
fi

if [ ! -z "$SGE_TASK_ID" ]
then
    # select-language-set logic
    # if it is a script - run it with sge-task-id parameter
    # else it is a text file - just extract a line dep. on task id

    if [ -x "$1" ]
    then
        lang_arr=( $( $1 $SGE_TASK_ID "${@:2}" ) )
    else
        [[ -z "$EXPERIMENT_SET" ]] && EXPERIMENT_SET=$1
        echo sge $SGE_TASK_ID
        line_no=$(( $SGE_TASK_ID % $(cat $1 | wc -l) +1 ))
        lang_arr=( $( sed "${line_no}q;d" $1 ) )
        echo line_no $line_no lang_arr ${lang_arr[@]}
    fi
elif [ $# -ne 0 ]
then
    lang_arr=( "$@" )
else
    exit 1
fi

IFS=$'\n' TARGET_LANGS=($(sort <<<"${lang_arr[*]}"))
unset IFS
TARGET_LANGS_STR=$(printf "%s" "${TARGET_LANGS[@]}")

# check if model aready converged
# TODO: get test results on convergence
CONVERGED="$(model_converged ${SOURCE_LANG} ${TARGET_LANGS_STR})"
[[ ! -z "${CONVERGED}" ]] && exit 0

# try to create a lock for this experiment
CREATE_LOCK_RESULT="$(create_lock ${SOURCE_LANG} ${TARGET_LANGS_STR})"
echo lock creation result: $CREATE_LOCK_RESULT ${CREATE_LOCK_RESULT}
IS_ALREADY_RUNNING="${CREATE_LOCK_RESULT}$(./full_jobs_names.sh | grep ${SOURCE_LANG}2{TARGET_LANGS_STR})"
echo Is already running: $IS_ALREADY_RUNNING
if [ ! -z "$IS_ALREADY_RUNNING" ]
then
    decrease_parent_concurrency $JOB_ID
    echo "Model ${SOURCE_LANG}2${TARGET_LANGS_STR} is already running, current task is aborted"
    exit 0
fi


if [ ! -e ./data/interim/${SOURCE_LANG}2${TARGET_LANGS_STR}.train.target ]
then
    mkdir -p run_logs
    prep_jid=$( qsub -b y -cwd -m n -N pr_${SOURCE_LANG}2${TARGET_LANGS_STR} \
        -j y -q cpu* -l mem_free=20G,act_mem_free=20G,h_vmem=30G \
        -o 'run_logs/$JOB_NAME.o$JOB_ID' \
        -terse \
        ./prepare_data.sh ${lang_arr[@]} )
    echo Preparing data. 
    echo $prep_jid is the ID
fi
[[ ! -z "$prep_jid" ]] && WAIT_FOR_PREP=" -hold_jid ${prep_jid} "
echo $WAIT_FOR_PREP

[[ ! -z "$TIME_LIMIT" ]] && [[ $TIME_LIMIT =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]] && TIME_RESOURCE=",h_rt=${TIME_LIMIT},s_rt=${TIME_LIMIT}"

echo ${TARGET_LANGS[@]}

# corpus creation is quite fast - so let's not occupy all the space
[[ ! -z "$SGE_TASK_ID" ]] && trap "echo cleaning data; rm -f ./data/interim/${SOURCE_LANG}2${TARGET_LANGS_STR}.*.*" EXIT

# if it is an array job - wait for a resp. gpu job
[[ ! -z "$SGE_TASK_ID" ]] && SYNC_JOB="-sync y"

# pass gpu cores number from config to qsub parameters
GPU=$(grep -A 8 devices config.yml | tr '\n' ' ' | sed 's/devices: \([0123456789 \-]*\).*/\1/g' | tr '-' '\n' | wc -l)
CPU=$(echo "${GPU} * 2" | bc)
if [ "$GPU" -gt 2 ]
then
    echo "Incorrect GPU number settings for this cluster, 2 is max"
    exit 1
fi
MEM=$(echo "${GPU} * 25" | bc)
echo "# of GPU's: ${GPU}"

[[ ! -z "$LOW_PRIORITY" ]] && PRIORITY='-p -200'
echo $PRIORITY priority

mkdir -p run_logs
logs_str='run_logs/$JOB_NAME.o$JOB_ID'
[[ ! -z "$SGE_TASK_ID" ]] && logs_str=$logs_str".$SGE_TASK_ID"
qsub -N "${SOURCE_LANG}2${TARGET_LANGS_STR}" -m n -j y -b y -cwd -q gpu* \
    -l gpu=${GPU},gpu_ram=8G,mem_free=${MEM}G,act_mem_free=${MEM}G,h_data=${MEM}G$TIME_RESOURCE \
    -pe smp ${CPU} \
    -o $logs_str \
    -v  SOURCE_LANG=$SOURCE_LANG \
    -v MARIAN=$MARIAN \
    -v EXPERIMENT_SET=$EXPERIMENT_SET \
    $WAIT_FOR_PREP \
    $PRIORITY \
    $SYNC_JOB \
    ./run-marian.sh ${TARGET_LANGS[@]}
