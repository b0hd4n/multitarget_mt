#!/bin/bash -v

# https://stackoverflow.com/a/17841619
function join_by { local IFS="$1"; shift; echo "$*"; }
function wandb_runner {
    echo Launching wandb runner...
    WANDB_PYTHON=../../envs/wandb_env/bin/python3
    WANDB_RUNNER=../../scripts/wandb_runner.py
    MODEL_DIR=$1
    [[ ! -z "$CLUSTER_NAME" ]] && TAGS=cluster:$CLUSTER_NAME || TAGS=cluster:undefined
    [[ ! -z "$EXPERIMENT_SET" ]] && TAGS=$TAGS,experiment:$EXPERIMENT_SET
    nohup $WANDB_PYTHON $WANDB_RUNNER --tags=$TAGS --infer-language-tags --wait-for-logs -d $MODEL_DIR &
    # &>/dev/null &
    RUNNER_PID=$!
    echo $RUNNER_PID WandD pid
    echo $TAGS
    sleep 15
    trap "echo stopping W&B runner; kill $RUNNER_PID" EXIT
}

echo CUDA_HOME:${CUDA_HOME}
nvcc --version

if [ ! $MARIAN ];
then
    echo MARIAN variable is not set, trying the default location '~/tools/marian'
    MARIAN=~/tools/marian
fi

# set chosen gpus
if [ ! $SOURCE_LANG ];
then
    echo SOURCE_LANG was not set, setting to default
	SOURCE_LANG=en;
fi

if [ ! $TARGET_LANGS ];
then
    echo TARGET_LANGS was not set, setting to default
    TARGET_LANGS=es
    TARGET_LANGS_STR=es;
else
    echo TARGET_LANGS has already been set
fi

if [ $# -ne 0 ]
then
    echo Setting TARGET_LANGS from parameters
    arr=( "$@" )
    IFS=$'\n' TARGET_LANGS=($(sort <<<"${arr[*]}"))
    unset IFS
    TARGET_LANGS_STR=$(printf "%s" "${TARGET_LANGS[@]}")
    echo $TARGET_LANGS_STR
fi

if [ ! -e $MARIAN/build/marian ]
then
    echo "marian is not installed in $MARIAN/build, you need to compile the toolkit first"
    exit 1
fi


# create the model folder
MODEL_NAME=${SOURCE_LANG}2${TARGET_LANGS_STR}
MODEL=model_${MODEL_NAME}
mkdir -p $MODEL

wandb_runner $MODEL
# WARNING! here's a hack to make validation script know about target languages
# another part is in script itself
cp ./validate.sh ${MODEL}/validate.sh

[[ -f $MODEL/train.source ]] || ln -s ../data/interim/${MODEL_NAME}.train.source $MODEL/train.source
[[ -f $MODEL/train.target ]] || ln -s ../data/interim/${MODEL_NAME}.train.target $MODEL/train.target
[[ -f $MODEL/val.source ]] || ln -s ../data/interim/${MODEL_NAME}.val.source $MODEL/val.source
[[ -f $MODEL/val.target ]] || ln -s ../data/interim/${MODEL_NAME}.val.target $MODEL/val.target

TRAIN_SOURCE=$MODEL/train.source
TRAIN_TARGET=$MODEL/train.target
VAL_SOURCE=$MODEL/val.source
VAL_TARGET=$MODEL/val.target

# train model
$MARIAN/build/marian \
    -c config.yml \
    --model $MODEL/model.npz \
    --train-sets ${TRAIN_SOURCE} ${TRAIN_TARGET} \
    --vocabs data/raw/vocab.multi.{yml,yml} \
    --valid-sets ${VAL_SOURCE} ${VAL_TARGET} \
	--valid-script-path ${MODEL}/validate.sh \
    --log $MODEL/train.log --valid-log $MODEL/valid.log --tempdir $MODEL
