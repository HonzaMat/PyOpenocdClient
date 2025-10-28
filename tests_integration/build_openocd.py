#!/usr/bin/python3

# SPDX-License-Identifier: MIT

import argparse
import multiprocessing
import os
import shutil
import subprocess
import sys
from pathlib import Path
from openocd_version_info import OPENOCD_VERSIONS, OPENOCD_VERSION_NAMES, OpenOcdVersion, LIBJIM_FROM_APT, LIBJIM_INTERNAL

# Build parallelism. (The upper limit is for safety.)
NPROC = min(multiprocessing.cpu_count(), 8)

initial_work_dir = Path(os.getcwd()).resolve()


def get_script_dir() -> Path:
    """Return path to the script directory."""
    return Path(__file__).resolve().parent


def get_src_dir(version: str, program: str) -> Path:
    """Return path to the directory with sources of OpenOCD or Jim Tcl."""
    return initial_work_dir / "src" / version / program


def get_install_dir(version: str, program: str) -> Path:
    """Return path to the directory with installed OpenOCD or Jim Tcl."""
    return initial_work_dir / "install" / version / program


def parse_args() -> OpenOcdVersion:
    desc = (
        "Script that downloads OpenOCD source code and performs the build. "
        "JimTcl is also built from source if needed."
    )
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--openocd-version",
        choices=OPENOCD_VERSION_NAMES,
        required=True,
        help="OpenOCD version to build"
    )
    args = parser.parse_args()

    assert args.openocd_version in OPENOCD_VERSION_NAMES
    return next(v for v in OPENOCD_VERSIONS if v.name == args.openocd_version)


def recreate_dir(d: Path) -> None:
    if d.exists():
        shutil.rmtree(d)
    os.makedirs(d)


def run_cmd(
    cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> None:
    print(f"Running command: {repr(cmd)} (work dir: {cwd})")
    subprocess.check_call(cmd, cwd=cwd, env=env)


def git_show_current_commit(cwd: Path) -> None:
    assert cwd.is_dir()
    run_cmd(["git", "--no-pager", "show", "--no-patch"], cwd=cwd)


def prepare_libjim(version: OpenOcdVersion) -> None:
    if version.libjim == LIBJIM_INTERNAL:
        # Do not install anything
        pass
    elif version.libjim == LIBJIM_FROM_APT:
        run_cmd(["sudo", "apt-get", "install", "-y", "libjim-dev"])
    else:
        checkout_and_build_libjim(version)


def checkout_and_build_libjim(version: OpenOcdVersion) -> None:
    assert version.libjim not in [LIBJIM_INTERNAL, LIBJIM_FROM_APT]
    assert not version.libjim.is_from_apt
    assert not version.libjim.is_internal
    assert version.libjim.repo is not None
    assert version.libjim.git_rev is not None

    src_dir = get_src_dir(version.name, "libjim")
    install_dir = get_install_dir(version.name, "libjim")
    recreate_dir(src_dir)
    recreate_dir(install_dir)

    run_cmd(["git", "clone", version.libjim.repo, "."], cwd=src_dir)
    run_cmd(["git", "checkout", version.libjim.git_rev], cwd=src_dir)
    git_show_current_commit(cwd=src_dir)

    configure_cmd = [
        "/bin/sh",
        "./configure",
        "--prefix=" + str(install_dir),
    ] + version.libjim.extra_configure_args
    run_cmd(configure_cmd, cwd=src_dir)

    run_cmd(["make", f"-j{NPROC}"], cwd=src_dir)
    run_cmd(["make", "install"], cwd=src_dir)

    # Make sure ./configure finds the just-built libjim library
    os.environ["PKG_CONFIG_PATH"] = str(install_dir / "lib" / "pkgconfig")


def checkout_and_build_openocd(version: OpenOcdVersion) -> None:
    src_dir = get_src_dir(version.name, "openocd")
    install_dir = get_install_dir(version.name, "openocd")
    recreate_dir(src_dir)
    recreate_dir(install_dir)

    run_cmd(["git", "clone", version.repo, "."], cwd=src_dir)
    run_cmd(["git", "checkout", version.git_rev], cwd=src_dir)
    git_show_current_commit(cwd=src_dir)

    if version.libjim == LIBJIM_INTERNAL:
        # Need to checkout the jimtcl submodule
        run_cmd(["git", "submodule", "update", "--init", "--recursive"], cwd=src_dir)

    run_cmd(["/bin/sh", "./bootstrap"], cwd=src_dir)

    configure_env = os.environ.copy()
    configure_env["CFLAGS"] = version.extra_cflags

    configure_cmd = ["/bin/sh", "./configure", "--prefix=" + str(install_dir)]
    configure_cmd += version.extra_configure_args

    run_cmd(configure_cmd, cwd=src_dir, env=configure_env)
    run_cmd(["make", f"-j{NPROC}"], cwd=src_dir)
    run_cmd(["make", "install"], cwd=src_dir)


def check_build(version: OpenOcdVersion) -> None:
    install_dir = get_install_dir(version.name, "openocd")

    openocd_bin = install_dir / "bin" / "openocd"
    if not openocd_bin.is_file():
        raise RuntimeError(
            f"The expected binary does not exist after the build: {str(openocd_bin)}"
        )

    run_cmd([str(openocd_bin), "--version"])

    print()
    print(f'OpenOCD "{version.name}" successfully built!')
    print(f"Path to the OpenOCD binary: {str(openocd_bin)}")


def main() -> int:
    openocd_version = parse_args()

    prepare_libjim(openocd_version)
    checkout_and_build_openocd(openocd_version)
    check_build(openocd_version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
