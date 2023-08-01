#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import re
import subprocess

# mamba not tested yet
conda_bin = os.environ.get("BLAS_CONDA", "conda")
# where we expect to find pip (generally not installed in the blas envs)
base_bindir = os.environ.get("BASE_ENV_BINDIR", ".")

env_specs = {
    "openblas_pthreads_lp64": ["libblas=*=*openblas", "openblas=*=pthreads*"],
    "openblas_pthreads_ilp64": ["openblas-ilp64=*=pthreads*"],
    "openblas_openmp_lp64": ["libblas=*=openblas", "openblas=*=openmp*"],
    "openblas_openmp_ilp64": ["openblas-ilp64=*=openmp*"],
    "netlib_pthreads": ["libblas=*=*netlib", "blas-devel=3.9.0=5*"],
    "blis_pthreads": ["libblas=*=*blis"],
    "mkl_openmp": ["libblas=*=*mkl"],
}
# add base-specs
base_spec = ["pip", "python=3.10", "ninja"]
env_specs = {k: v + base_spec for k, v in env_specs.items()}


# not exposed in CLI
def _exists(env):
    if env is None:
        raise ValueError("Must provide an environment!")
    # need subprocess.run to be able to capture output;
    # `conda env list --json` shows only paths, not names
    res = subprocess.run([conda_bin, "env", "list"], capture_output=True)
    # don"t match on partial names; from beginning (^) to following space (\s+)
    return any(re.match(rf"^{env}\s+", x) for x in res.stdout.decode("utf-8").splitlines())


def _is_active(env):
    if env is None:
        raise ValueError("Must provide an environment!")
    # need subprocess.run to be able to capture output
    res = subprocess.run([conda_bin, "info", "--json"], capture_output=True)
    content = json.loads(res.stdout.decode("utf-8"))
    # don"t match on partial names; from beginning (^) to following space (\s+)
    return content["active_prefix_name"] == env


def _do_teardown(env):
    if not _exists(env):
        print(f"Environment {env} does not exist, skipping...")
    else:
        subprocess.call([conda_bin, "env", "remove", "-n", env, "-y"])


def _do_spinup(env, force):
    if env not in env_specs.keys():
        raise RuntimeError(f"Unknown environment specified: {env}!\n"
                           f"Known environments: {', '.join(env_specs.keys())}")
    if _exists(env) and not force:
        print(f"Environment {env} exists already, and --force not specified, skipping...")
        return

    if _exists(env):
        _do_teardown(env)
    ret = subprocess.call([conda_bin, "create", "-n", env, *(env_specs[env]), "-y"])
    if ret:
        raise RuntimeError("Error occurred during environment creation!")
    subprocess.call([f"{base_bindir}/pip", "install", "-e", "."])


# cannot do this (sanely) from python; use bash
# def activate(args):
#     pass


def test(args):
    if args.env is None:
        raise ValueError("Can only run tests when given an environment!")
    if not _is_active(args.env):
        raise ValueError(f"Environment {args.env} must be activated for testing!")
    print(f"Running tests in {args.env}")
    # point this to respective blas test
    subprocess.call([f"{base_bindir}/python", "run_unittests.py"])


def list_envs(args):
    # following `conda list` and `conda env list`
    print(" ".join(env_specs.keys()))


def spinup(args):
    msg = "all the envs" if args.env is None else args.env
    print(f"Setting up {msg}!")
    if args.env is None:
        for e in env_specs.keys():
            _do_spinup(e, args.force)
    else:
        _do_spinup(args.env, args.force)


def teardown(args):
    msg = "all the envs" if args.env is None else args.env
    print(f"Removing {msg}!")
    if args.env is None:
        question = "Are you sure you want to delete all environments? y/n\n"
        while True:
            if answer := input(question).lower() in ["y", "n"]:
                break
        if answer == "n":
            return
        for e in env_specs.keys():
            _do_teardown(e)
    else:
        _do_teardown(args.env)


# top-level parser
parser = argparse.ArgumentParser()
main_verbs = parser.add_subparsers(required=True)

# parser for the "test" subcommand
p_test = main_verbs.add_parser("test")
p_test.add_argument("env", help="the environment to test")
p_test.set_defaults(func=test)

# parser for the "spinup" subcommand
p_spinup = main_verbs.add_parser("spinup")
p_spinup.add_argument("env", nargs="?", help="the environment to spinup")
p_spinup.add_argument('--force', action="store_true", help="force or not")
p_spinup.set_defaults(func=spinup)

# parser for the "teardown" subcommand
p_teardown = main_verbs.add_parser("teardown")
p_teardown.add_argument("env", nargs="?", help="the environment to teardown")
p_teardown.set_defaults(func=teardown)

# parser for the "list" subcommand
p_list = main_verbs.add_parser("list")
p_list.set_defaults(func=list_envs)


if __name__ == "__main__":
    parser.parse_args()

    # parse the args and call whatever function was selected
    args = parser.parse_args()
    args.func(args)
