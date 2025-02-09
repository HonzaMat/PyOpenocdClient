#!/usr/bin/python3

import argparse
import multiprocessing
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_OPENOCD_VANILLA = "https://github.com/openocd-org/openocd.git"
REPO_OPENOCD_RISCV = "https://github.com/riscv-collab/riscv-openocd.git"

REPO_LIBJIM = "https://github.com/msteveb/jimtcl.git"
LIBJIM_CONFIGURE_ARGS = ["--with-ext=json", "--minimal", "--disable-ssl"]

LIBJIM_FROM_APT = "apt"
LIBJIM_FROM_SOURCE_0_83 = "0.83"

BUILD_INFO = {
    "vanilla-v0.10.0": {
        "repo": REPO_OPENOCD_VANILLA,
        "git_rev": "v0.10.0",
        "extra_cflags": "-Wno-error",
        "libjim_version": None,
    },
    "vanilla-v0.11.0": {
        "repo": REPO_OPENOCD_VANILLA,
        "git_rev": "v0.11.0",
        "extra_cflags": "-Wno-error",
        "libjim_version": None,
    },
    "vanilla-v0.12.0": {
        "repo": REPO_OPENOCD_VANILLA,
        "git_rev": "v0.12.0",
        "extra_cflags": "",
        "libjim_version": None,
    },
    "vanilla-master-default-libjim": {
        "repo": REPO_OPENOCD_VANILLA,
        "git_rev": "master",
        "extra_cflags": "",
        "libjim_version": LIBJIM_FROM_APT,
    },
    "vanilla-master-libjim-0.83": {
        "repo": REPO_OPENOCD_VANILLA,
        "git_rev": "master",
        "extra_cflags": "",
        "libjim_version": LIBJIM_FROM_SOURCE_0_83,
    },
    "riscv-master-default-libjim": {
        "repo": REPO_OPENOCD_RISCV,
        "git_rev": "riscv",
        "extra_cflags": "",
        "libjim_version": LIBJIM_FROM_APT,
    },
    "riscv-master-libjim-0.83": {
        "repo": REPO_OPENOCD_RISCV,
        "git_rev": "riscv",
        "extra_cflags": "",
        "libjim_version": LIBJIM_FROM_SOURCE_0_83,
    },
}

KNOWN_VERSIONS = list(BUILD_INFO.keys())

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "version", choices=KNOWN_VERSIONS, help="OpenOCD version to build"
    )
    return parser.parse_args()


def recreate_dir(d: Path):
    if d.exists():
        shutil.rmtree(d)
    os.makedirs(d)


def run_cmd(cmd: list[str], cwd: str | None = None, env=None) -> None:
    print(f"Running command: {repr(cmd)} (work dir: {cwd})")
    subprocess.check_call(cmd, cwd=cwd, env=env)


def prepare_libjim(version: str) -> None:
    libjim_version = BUILD_INFO[version]["libjim_version"]

    if libjim_version is None:
        return
    elif libjim_version == LIBJIM_FROM_APT:
        run_cmd(["sudo", "apt-get", "install", "-y", "libjim-dev"])
    else:
        checkout_and_build_libjim(version)


def checkout_and_build_libjim(version: str) -> None:
    src_dir = get_src_dir(version, "libjim")
    install_dir = get_install_dir(version, "libjim")
    recreate_dir(src_dir)
    recreate_dir(install_dir)

    run_cmd(["git", "clone", REPO_LIBJIM, "."], cwd=src_dir)
    run_cmd(["git", "checkout", BUILD_INFO[version]["libjim_version"]], cwd=src_dir)
    run_cmd(
        ["git", "--no-pager", "show", "--no-patch"], cwd=src_dir
    )  # show current commit

    configure_cmd = [
        "/bin/sh",
        "./configure",
        "--prefix=" + str(install_dir),
    ] + LIBJIM_CONFIGURE_ARGS
    run_cmd(configure_cmd, cwd=src_dir)

    nproc = min(multiprocessing.cpu_count(), 8)  # safety
    run_cmd(["make", f"-j{nproc}"], cwd=src_dir)
    run_cmd(["make", "install"], cwd=src_dir)


def checkout_and_build_openocd(version: str) -> None:
    src_dir = get_src_dir(version, "openocd")
    install_dir = get_install_dir(version, "openocd")
    recreate_dir(src_dir)
    recreate_dir(install_dir)

    run_cmd(["git", "clone", BUILD_INFO[version]["repo"], "."], cwd=src_dir)
    run_cmd(["git", "checkout", BUILD_INFO[version]["git_rev"]], cwd=src_dir)
    run_cmd(
        ["git", "--no-pager", "show", "--no-patch"], cwd=src_dir
    )  # show current commit
    run_cmd(["git", "submodule", "update", "--init", "--recursive"], cwd=src_dir)
    run_cmd(["/bin/sh", "./bootstrap"], cwd=src_dir)

    extra_cflags = BUILD_INFO[version]["extra_cflags"]

    env = os.environ.copy()
    env["CFLAGS"] = extra_cflags

    libjim_is_from_source = BUILD_INFO[version]["libjim_version"] not in [
        None,
        LIBJIM_FROM_APT,
    ]
    if libjim_is_from_source:
        env["PKG_CONFIG_PATH"] = (
            get_install_dir(version, "libjim") / "lib" / "pkgconfig"
        )

    run_cmd(
        ["/bin/sh", "./configure", "--prefix=" + str(install_dir)], cwd=src_dir, env=env
    )

    nproc = min(multiprocessing.cpu_count(), 8)  # safety
    run_cmd(["make", f"-j{nproc}"], cwd=src_dir)
    run_cmd(["make", "install"], cwd=src_dir)


def check_build(version: str) -> None:
    install_dir = get_install_dir(version, "openocd")

    openocd_bin = install_dir / "bin" / "openocd"
    if not openocd_bin.is_file():
        raise RuntimeError(
            f"Expected binary does not exist after the build: {str(openocd_bin)}"
        )

    run_cmd([openocd_bin, "--version"])
    print(f'OpenOCD "{version}" successfully built: {str(openocd_bin)}')


def main() -> int:
    args = parse_args()

    prepare_libjim(args.version)
    checkout_and_build_openocd(args.version)
    check_build(args.version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
