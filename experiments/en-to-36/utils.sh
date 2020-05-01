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
    # returns lock file name if created successfully
    local SRC=$1
    local TGTS=$2
    mkdir -p locks
    local LOCKFILE=locks/${SRC}2${TGTS}.lock
    lockfile -r 0 ${LOCKFILE}
    local result="$?"

    if [ "${result}" != "0" ]
    then
        1>&2 echo non-zero result: ${result};
    else
        1>&2 echo result: ${result}, lock is created;
        echo $LOCKFILE
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

# trap_add from https://stackoverflow.com/a/7287873`
# note: printf is used instead of echo to avoid backslash
# processing and to properly handle values that begin with a '-'.
log() { printf '%s\n' "$*"; }
error() { log "ERROR: $*" >&2; }
fatal() { error "$@"; exit 1; }
# appends a command to a trap
#
# - 1st arg:  code to add
# - remaining args:  names of traps to modify
#
trap_add() {
    trap_add_cmd=$1; shift || fatal "${FUNCNAME} usage error"
    for trap_add_name in "$@"; do
        trap -- "$(
            # helper fn to get existing trap command from output
            # of trap -p
            extract_trap_cmd() { printf '%s\n' "$3"; }
            # print existing trap command with newline
            eval "extract_trap_cmd $(trap -p "${trap_add_name}")"
            # print the new trap command
            printf '%s\n' "${trap_add_cmd}"
        )" "${trap_add_name}" \
            || fatal "unable to add to trap ${trap_add_name}"
    done
}
# set the trace attribute for the above function.  this is
# required to modify DEBUG or RETURN traps because functions don't
# inherit them unless the trace attribute is set
declare -f -t trap_add
