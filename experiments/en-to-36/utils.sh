function decrease_parent_concurrency {
    local JOB_ID=$1
    echo JOB_ID: $JOB_ID

    local PARENT_CONCURRENCY=$(qstat -j $JOB_ID | grep 'concurrency' | sed -e 's/.*\([0-9]\{1,\}\)/\1/g')
    echo $PARENT_CONCURRENCY
    if [ ! -z $PARENT_CONCURRENCY ]
    then
        echo Decreasing parent\'s concurrency...
        qalter -tc $(("$PARENT_CONCURRENCY"-1)) $JOB_ID
        echo done.
    else
        echo Failed to decrease $JOB_ID parent\'s concurrency
    fi
}

function create_lock {
    # lock was not created if output is not empty
    local SRC=$1
    local TGTS=$2
    mkdir -p locks
    local LOCKFILE=locks/${SRC}2${TGTS}.lock
    local result="$(lockfile -r 0 ${LOCKFILE} || echo Locked )"

    if [ ! -z "${result}" ]
    then
        echo ${result}
    else
	trap "rm -f $LOCKFILE" EXIT
    fi
}

function model_converged {
    # model is not converged if output is empty
    local SRC=$1
    local TGTS=$2

    if [ -e ./model_${SRC}2${TGTS}/train.log ]
    then
        local CONVERGED=$(cat ./model_${SOURCE_LANG}2${TARGET_LANGS_STR}/train.log | grep 'Training finished' | wc -l)
        [[ "${CONVERGED}" !=  "0" ]] && echo "Model ${SOURCE_LANG}2${TARGET_LANGS_STR} has already converged"
    fi
}
