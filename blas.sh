#!/bin/bash
set -e

CONDA_BIN=${BLAS_CONDA:-conda}
PYTHON_BIN=$(which python)
BLAS_CLICK_WRAPPER="${PYTHON_BIN} _blas.py"
# need to pass this to python script
export BASE_ENV_BINDIR=$(dirname $PYTHON_BIN)

# we need to ensure our current process (in which this script is running) can
# find the activation mechanisms usually these are inserted into ~/.bashrc,
# but in this shell, this isn't loaded.
# Extract the part that `conda init` has inserted (which conveniently has
# markers around it); ensure sed-replacement can deal with multiline, see
# https://unix.stackexchange.com/a/152389
if [ ! -f .localinitrc ]; then
    extract=$(cat ~/.bashrc | tr '\n' '\f' | sed -E 's/.*\# >>> conda initialize >>>(.*)\# <<< conda initialize <<<.*/\1/g' | tr '\f' '\n')
    echo "$extract" > .localinitrc
fi
# run extracted bits it in this process
source .localinitrc


function activate_or_delegate()
{
    # echo "got $1 as first argument"
    case "$1" in
    activate)
        # environment activation is essentially impossible to do sanely from python
        $CONDA_BIN "$@"
        ;;
    test)
        shift  # strip off "test" from arguments
        $CONDA_BIN activate "$1"
        # interface break here... bash blas.sh test <env> vs. python _blas.py test --env=<env>
        # would be nice to get rid of this, but needs deeper click changes
        $BLAS_CLICK_WRAPPER test "$@"
        ;;
    *)
        # delegate to python CLI
        $BLAS_CLICK_WRAPPER "$@"
        ;;
    esac
}


case "$1" in
test_all)
    # needs to loop over all environments, and so cannot be in
    # same switch-statement as activation
    envs=$($BLAS_CLICK_WRAPPER list)
    envs_array=($envs)
    for env in "${envs_array[@]}"; do
        activate_or_delegate test "$env"
    done
    ;;
*)
    # everything else
    activate_or_delegate "$@"
    ;;
esac
