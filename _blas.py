#!/usr/bin/env python3

import json
import os
import pathlib
import re
import subprocess

import click

# mamba not tested yet
conda_bin = os.environ.get("BLAS_CONDA", "conda")
# where we expect to find pip (generally not installed in the blas envs)
base_bindir = os.environ.get("BASE_ENV_BINDIR", ".")

env_specs = {
    "linux_openblas_pthreads_lp64": "libblas=*=*openblas openblas=*=pthreads*",
    "linux_openblas_pthreads_ilp64": "openblas-ilp64=*=pthreads*",
    "linux_openblas_openmp_lp64": "libblas=*=openblas openblas=*=openmp*",
    "linux_openblas_openmp_ilp64": "openblas-ilp64=*=openmp*",
    "linux_netlib_pthreads": "libblas=*=*netlib blas-devel=3.9.0=5*",
    "linux_blis_pthreads": "libblas=*=*blis",
    "linux_mkl_openmp": "libblas=*=*mkl",
}


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
        click.echo(f"Environment {env} does not exist, skipping...")
    else:
        subprocess.call([conda_bin, "env", "remove", "-n", env, "-y"])


def _do_spinup(env, force):
    if env not in env_specs.keys():
        raise RuntimeError(f"Unknown environment specified: {env}!\n"
                           f"Known environments: {', '.join(env_specs.keys())}")
    if _exists(env) and not force:
        click.echo(f"Environment {env} exists already, and --force not specified, skipping...")
        return

    if _exists(env):
        _do_teardown(env)
    ret = subprocess.call([conda_bin, "create", "-n", env, env_specs[env], "-y"])
    if ret:
        raise RuntimeError("Error occurred during environment creation!")
    subprocess.call([f"{base_bindir}/pip", "install", "-e", "."])


@click.group()
def mygroup(ctx):
    pass


# cannot do this (sanely) from python; use bash
# def activate(env):
#     pass


@mygroup.command()
@click.option("--env", default=None)
def test(env):
    if env is None:
        raise ValueError("Can only run tests when given an environment!")
    if not _is_active(env):
        raise ValueError(f"Environment {env} must be activated for testing!")
    click.echo(f"Running tests in {env}")
    # point this to respective blas test
    subprocess.call([f"{base_bindir}/python", "run_unittests.py"])


@mygroup.command()
def list():
    # following `conda list` and `conda env list`
    click.echo(" ".join(env_specs.keys()))


@mygroup.command()
@click.option("--env", default=None)
@click.option("--force", default=False, is_flag=True)
def spinup(env, force):
    msg = "all the envs" if env is None else env
    click.echo(f"Setting up {msg}!")
    if env is None:
        for env in env_specs.keys():
            _do_spinup(env, force)
    else:
        _do_spinup(env, force)


@mygroup.command()
@click.option("--env", default=None)
def teardown(env):
    msg = "all the envs" if env is None else env
    click.echo(f"Removing {msg}!")
    if env is None:
        for env in env_specs.keys():
            _do_teardown(env)
    else:
        _do_teardown(env)


cli = click.CommandCollection(sources=[mygroup])

if __name__ == "__main__":
    cli()
