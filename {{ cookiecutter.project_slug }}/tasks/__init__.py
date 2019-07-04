# -*- coding: utf-8 -*-
import pathlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import invoke
import parver


ROOT = Path(__file__).resolve().parent.parent

PACKAGE_NAME = '{{ cookiecutter.package_name }}'

INIT_PY = ROOT.joinpath('src', PACKAGE_NAME, '__init__.py')


def _get_git_root(ctx):
    return Path(ctx.run("git rev-parse --show-toplevel", hide=True).stdout.strip())


@invoke.task()
def typecheck(ctx):
    src_dir = ROOT / "src" / PACKAGE_NAME
    src_dir = src_dir.as_posix()
    config_file = ROOT / "setup.cfg"
    env = {"MYPYPATH": src_dir}
    ctx.run(f"mypy {src_dir} --config-file={config_file}", env=env)


@invoke.task()
def clean(ctx):
    """Clean previously built package artifacts.
    """
    ctx.run(f"python setup.py clean")
    dist = ROOT.joinpath("dist")
    build = ROOT.joinpath("build")
    print(f"[clean] Removing {dist} and {build}")
    if dist.exists():
        shutil.rmtree(str(dist))
    if build.exists():
        shutil.rmtree(str(build))


def find_version():
    version_file = INIT_PY.read_text()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def _read_version():
    out = subprocess.check_output(['git', 'tag'], encoding='ascii')
    try:
        version = max(parver.Version.parse(v).normalize() for v in (
            line.strip() for line in out.split('\n')
        ) if v)
    except ValueError:
        version = parver.Version.parse('0.0.0')
    return version


def _write_version(v):
    lines = []
    with INIT_PY.open() as f:
        for line in f:
            if line.startswith("__version__ = "):
                line = f"__version__ = {repr(str(v))}\n".replace("'", '"')
            lines.append(line)
    with INIT_PY.open("w", newline="\n") as f:
        f.write("".join(lines))


REL_TYPES = ("major", "minor", "patch", "post")


def _prebump(version, prebump, log=False):
    next_version = version.bump_release(index=prebump).bump_dev()
    if log:
        print(f"[bump] {version} -> {next_version}")
    print(f"{next_version}")
    return next_version


PREBUMP = 'patch'


@invoke.task(pre=[clean])
def build(ctx):
    ctx.run("python setup.py sdist bdist_wheel")


@invoke.task()
def get_next_version(ctx, type_="patch", log=False):
    version = _read_version()
    if type_ in ("dev", "pre"):
        idx = REL_TYPES.index("patch")
        new_version = _prebump(version, idx, log=log)
    else:
        new_version = _bump_release(version, type_, log=log)
    return new_version


@invoke.task()
def bump_version(ctx, type_="patch", log=False, dry_run=False):
    new_version = get_next_version(ctx, type_, log=log)
    if not dry_run:
        _write_version(new_version)
    return new_version


def _bump_release(version, type_, log=False):
    if type_ not in REL_TYPES:
        raise ValueError(f"{type_} not in {REL_TYPES}")
    index = REL_TYPES.index(type_)
    next_version = version.base_version().bump_release(index=index)
    if log:
        print(f"[bump] {version} -> {next_version}")
    print(f"{next_version}")
    return next_version


@invoke.task(optional=["version", "type_"])
def tag_release(ctx, version=None, type_="patch", yes=False, dry_run=False):
    if version is None:
        version = bump_version(ctx, type_, log=not dry_run, dry_run=dry_run)
    else:
        _write_version(version)
    git_commit_cmd = f'git commit -am "Release {version}"'
    git_tag_cmd = f'git tag -a {version} -m "Version {version}"'
    if dry_run:
        print("Would run commands:")
        print(f"    {git_commit_cmd}")
        print(f"    {git_tag_cmd}")
    else:
        ctx.run(git_commit_cmd)
        ctx.run(git_tag_cmd)


@invoke.task(pre=[clean])
def release(ctx, type_, repo, prebump=PREBUMP, yes=False):
    """Make a new release.
    """
    if prebump not in REL_TYPES:
        raise ValueError(f"{type_} not in {REL_TYPES}")
    prebump = REL_TYPES.index(prebump)

    version = bump_version(ctx, type_, log=True)
    # Needs to happen before Towncrier deletes fragment files.
    tag_release(version, yes=yes)

    ctx.run(f"python setup.py sdist bdist_wheel")

    dist_pattern = f'{PACKAGE_NAME.replace("-", "[-_]")}-*'
    artifacts = list(ROOT.joinpath("dist").glob(dist_pattern))
    filename_display = "\n".join(f"  {a}" for a in artifacts)
    print(f"[release] Will upload:\n{filename_display}")
    if not yes:
        try:
            input("[release] Release ready. ENTER to upload, CTRL-C to abort: ")
        except KeyboardInterrupt:
            print("\nAborted!")
            return

    arg_display = " ".join(f'"{n}"' for n in artifacts)
    ctx.run(f'twine upload --repository="{repo}" {arg_display}')

    version = _prebump(version, prebump)
    _write_version(version)

    ctx.run(f'git commit -am "Prebump to {version}"')
