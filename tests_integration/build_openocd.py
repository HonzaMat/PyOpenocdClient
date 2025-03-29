#!/usr/bin/python3

import argparse
from dataclasses import dataclass
from enum import Enum
import multiprocessing
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_OPENOCD_VANILLA = "https://github.com/openocd-org/openocd.git"
REPO_OPENOCD_RISCV = "https://github.com/riscv-collab/riscv-openocd.git"

REPO_LIBJIM = "https://github.com/msteveb/jimtcl.git"
LIBJIM_CONFIGURE_ARGS = ["--with-ext=json", "--disable-ssl"]

# Build parallelism. (The upper limit is for safety.)
NPROC = min(multiprocessing.cpu_count(), 8)


class LibJimVersion(Enum):
    FROM_APT = "apt"
    INTERNAL = "internal"  # From submodule in OpenOCD repo
    FROM_SOURCE_0_79 = "0.79"  # Used in Debian 11
    FROM_SOURCE_0_83 = "0.83"


@dataclass
class OpenOcdVersion:
    name: str
    repo: str
    git_rev: str
    extra_cflags: str
    extra_configure_args: list[str]
    libjim: LibJimVersion


# Various combinations of:
# - OpenOCD version
# - JimTcl version
OPENOCD_VERSIONS = [
    OpenOcdVersion(
        name="vanilla-0.10.0",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="v0.10.0",
        # Older OpenOCD code has compilation warnings on new GCC
        extra_cflags="-Wno-error",
        extra_configure_args=[],
        libjim=LibJimVersion.INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-0.11.0",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="v0.11.0",
        # Older OpenOCD code has compilation warnings on new GCC
        extra_cflags="-Wno-error",
        extra_configure_args=[],
        libjim=LibJimVersion.INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-0.12.0",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="v0.12.0",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LibJimVersion.INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-from-apt",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LibJimVersion.FROM_APT,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-internal",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=["--enable-internal-jimtcl"],
        libjim=LibJimVersion.INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-0.79",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LibJimVersion.FROM_SOURCE_0_79,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-0.83",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LibJimVersion.FROM_SOURCE_0_83,
    ),
    OpenOcdVersion(
        name="riscv-master-libjim-from-apt",
        repo=REPO_OPENOCD_RISCV,
        git_rev="riscv",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LibJimVersion.FROM_APT,
    ),
]

OPENOCD_VERSION_NAMES = [v.name for v in OPENOCD_VERSIONS]

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
        "Script that downloads OpenOCD source code and performs the from-source build. "
        "JimTcl is also built from source if needed."
    )
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "version_name", choices=OPENOCD_VERSION_NAMES, help="OpenOCD version to build"
    )
    args = parser.parse_args()

    assert args.version_name in OPENOCD_VERSION_NAMES
    return next(v for v in OPENOCD_VERSIONS if v.name == args.version_name)


def recreate_dir(d: Path):
    if d.exists():
        shutil.rmtree(d)
    os.makedirs(d)


def run_cmd(cmd: list[str], cwd: str | None = None, env=None) -> None:
    print(f"Running command: {repr(cmd)} (work dir: {cwd})")
    subprocess.check_call(cmd, cwd=cwd, env=env)


def git_show_current_commit(cwd: Path) -> None:
    assert cwd.is_dir()
    run_cmd(
        ["git", "--no-pager", "show", "--no-patch"], cwd=cwd
    )


def prepare_libjim(libjim_version: LibJimVersion) -> None:
    if libjim_version == LibJimVersion.INTERNAL:
        # Do not install anything
        pass
    elif libjim_version == LibJimVersion.FROM_APT:
        run_cmd(["sudo", "apt-get", "install", "-y", "libjim-dev"])
    else:
        checkout_and_build_libjim(libjim_version)


def checkout_and_build_libjim(libjim_version: LibJimVersion) -> None:
    assert libjim_version not in [LibJimVersion.INTERNAL, LibJimVersion.FROM_APT]

    libjim_rev = libjim_version.value

    src_dir = get_src_dir(libjim_rev, "libjim")
    install_dir = get_install_dir(libjim_rev, "libjim")
    recreate_dir(src_dir)
    recreate_dir(install_dir)

    run_cmd(["git", "clone", REPO_LIBJIM, "."], cwd=src_dir)
    run_cmd(["git", "checkout", libjim_rev], cwd=src_dir)
    git_show_current_commit(cwd=src_dir)

    configure_cmd = [
        "/bin/sh",
        "./configure",
        "--prefix=" + str(install_dir),
    ] + LIBJIM_CONFIGURE_ARGS
    run_cmd(configure_cmd, cwd=src_dir)

    run_cmd(["make", f"-j{NPROC}"], cwd=src_dir)
    run_cmd(["make", "install"], cwd=src_dir)

    # Make sure ./configure finds the built libjim library
    os.environ["PKG_CONFIG_PATH"] = str(install_dir / "lib" / "pkgconfig")


def checkout_and_build_openocd(version: OpenOcdVersion) -> None:
    src_dir = get_src_dir(version.name, "openocd")
    install_dir = get_install_dir(version.name, "openocd")
    recreate_dir(src_dir)
    recreate_dir(install_dir)

    run_cmd(["git", "clone", version.repo, "."], cwd=src_dir)
    run_cmd(["git", "checkout", version.git_rev], cwd=src_dir)
    git_show_current_commit(cwd=src_dir)

    if version.libjim == LibJimVersion.INTERNAL:
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

    run_cmd([openocd_bin, "--version"])

    print()
    print(f'OpenOCD "{version.name}" successfully built!')
    print(f"Path to the OpenOCD binary: {str(openocd_bin)}")


def main() -> int:
    openocd_version = parse_args()

    prepare_libjim(openocd_version.libjim)
    checkout_and_build_openocd(openocd_version)
    check_build(openocd_version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
