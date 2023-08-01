BLAS Testing
============

Main interface is through bash, because activation from python is essentially impossible

- bash blas.sh test                                  # run the test for all environments
- bash blas.sh test <env_name>                       # run the test for a specific environment
- bash blas.sh activate <env_name>                   # doesn't really do anything, because after script end it's gone again
- bash blas.sh spinup                                # creates all environments that haven't been created yet
- bash blas.sh spinup --force                        # force recreates all environments
- bash blas.sh spinup <env_name>  [--force]          # spin up particular environment
- bash blas.sh teardown                              # tear down all environments
- bash blas.sh teardown <env_name>                   # tear down particular environment
- bash blas.sh list                                  # list all specified environments

Where reasonable, the interface is implemented in argparse, which is called through bash,
but can be called directly where desired
- python _blas.py spinup <env_name> ...
