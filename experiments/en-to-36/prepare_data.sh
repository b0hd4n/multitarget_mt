#!/bin/bash 

function join_by { local IFS="$1"; shift; echo "$*"; }

if [ $# -ne 0 ]
then
    arr=( "$@" )
    IFS=$'\n' TARGET_LANGS=($(sort <<<"${arr[*]}"))
    unset IFS
    TARGET_LANGS_STR=$(printf "%s" "${TARGET_LANGS[@]}")

    TARGET_LANGS_REGEX=$(printf "\\|%s" "${TARGET_LANGS[@]}")
    TARGET_LANGS_REGEX="<2\\(${TARGET_LANGS_REGEX:2}\\)>"
fi

echo $TARGET_LANGS_REGEX

# Training set
paste data/processed/train.src data/processed/train.tgt \
    | grep -e $TARGET_LANGS_REGEX \
    | awk -F'\t' -v f="data/interim/en2"${TARGET_LANGS_STR}".train" '{print $1 > f ".source"; print $2 > f ".target" }' 

# Validation set
paste data/processed/dev.src data/processed/dev.tgt \
    | grep -e $TARGET_LANGS_REGEX \
    | awk -F'\t' -v f="data/interim/en2"${TARGET_LANGS_STR}".val" '{print $1 > f ".source"; print $2 > f ".target" }' 

