#!/usr/bin/python3

# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field

REPO_OPENOCD_VANILLA = "https://github.com/openocd-org/openocd.git"
REPO_OPENOCD_RISCV = "https://github.com/riscv-collab/riscv-openocd.git"

REPO_LIBJIM = "https://github.com/msteveb/jimtcl.git"


@dataclass
class LibJimVersion:
    is_internal: bool = False
    is_from_apt: bool = False
    repo: str | None = None
    git_rev: str | None = None
    extra_configure_args: list[str] = field(default_factory=lambda: [])


LIBJIM_FROM_APT = LibJimVersion(is_from_apt=True)
LIBJIM_INTERNAL = LibJimVersion(is_internal=True)
LIBJIM_FROM_SOURCE_0_79 = LibJimVersion(
    # JimTcl version used in Debian 11
    repo=REPO_LIBJIM,
    git_rev="0.79",
    extra_configure_args=["--with-ext=json", "--disable-ssl"],
)
LIBJIM_FROM_SOURCE_0_83 = LibJimVersion(
    # Latest JimTcl release as of March 2025
    repo=REPO_LIBJIM,
    git_rev="0.83",
    extra_configure_args=["--with-ext=json", "--disable-ssl", "--minimal"],
)


@dataclass
class OpenOcdVersion:
    name: str
    repo: str
    git_rev: str
    extra_cflags: str
    extra_configure_args: list[str]
    libjim: LibJimVersion


# Various combinations of OpenOCD and JimTcl versions that we test against:
OPENOCD_VERSIONS = [
    OpenOcdVersion(
        name="vanilla-0.10.0",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="v0.10.0",
        # Older OpenOCD code has compilation warnings on new GCC
        extra_cflags="-Wno-error",
        extra_configure_args=[],
        libjim=LIBJIM_INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-0.11.0",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="v0.11.0",
        # Older OpenOCD code has compilation warnings on new GCC
        extra_cflags="-Wno-error",
        extra_configure_args=[],
        libjim=LIBJIM_INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-0.12.0",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="v0.12.0",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LIBJIM_INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-from-apt",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LIBJIM_FROM_APT,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-internal",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=["--enable-internal-jimtcl"],
        libjim=LIBJIM_INTERNAL,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-0.79",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LIBJIM_FROM_SOURCE_0_79,
    ),
    OpenOcdVersion(
        name="vanilla-master-libjim-0.83",
        repo=REPO_OPENOCD_VANILLA,
        git_rev="master",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LIBJIM_FROM_SOURCE_0_83,
    ),
    OpenOcdVersion(
        name="riscv-master-libjim-from-apt",
        repo=REPO_OPENOCD_RISCV,
        git_rev="riscv",
        extra_cflags="",
        extra_configure_args=[],
        libjim=LIBJIM_FROM_APT,
    ),
]

OPENOCD_VERSION_NAMES = [v.name for v in OPENOCD_VERSIONS]
