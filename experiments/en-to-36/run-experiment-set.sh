#!/usr/bin/env bash

if [ ! $# -ne 0 ]
then
    echo "Usage: ./run-experiment-set.sh setups_list.txt <num_of_jobs> <offset>"
    echo "       ./run-experiment-set.sh setups_generator.py <num_of_jobs> <offset>"
    echo "       TIME_LIMIT=00:10:00 ./run-experiment-set.sh setups_list.txt <num_of_jobs> <offset>"
    exit 1
fi

[[ -z "$3" ]] && OFFSET=0 || OFFSET=$3
FROM=$((1+"${OFFSET}"))
TO=$(( "${2}"+"${OFFSET}" ))
echo $FROM to $TO

[[ -z "$CONC_TASKS" ]] && CONC_TASKS=1
echo $CONC_TASKS

# set up time limit for each job
[[ ! -z "$TIME_LIMIT" ]] && [[ $TIME_LIMIT =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]] || TIME_LIMIT='00:05:00'

qsub -b y -cwd -m n -N aj_${1/\//_} \
        -j y -q cpu* \
        -t $FROM-$TO \
        -o "logs" \
        -v TIME_LIMIT=$TIME_LIMIT \
        -v LOW_PRIORITY="$LOW_PRIORITY" \
	-v MARIAN=$MARIAN \
        -tc $CONC_TASKS \
        ./run-experiment.sh "$@"
