from pathlib import Path

import nox


def _this_dir():
    """Return path to the script directory."""
    return Path(__file__).resolve().parent


def _run_isort(session, targets, make_edits):
    cmd = ["python3", "-m", "isort", "--profile", "black"]
    if not make_edits:
        cmd += ["--check-only", "--diff"]
    cmd += map(str, targets)
    session.run(*cmd)


def _run_black(session, targets, make_edits):
    cmd = ["python3", "-m", "black", "-q"]
    if not make_edits:
        cmd += ["--check", "--diff"]
    cmd += map(str, targets)
    session.run(*cmd)


def _run_flake8(session, targets):
    cmd = [
        "python3",
        "-m",
        "flake8",
        "--max-line-length",
        "88",
        "--extend-ignore",
        "E203",
    ]
    cmd += map(str, targets)
    session.run(*cmd)


def _run_mypy(session, targets):
    for t in targets:
        session.run("python3", "-m", "mypy", "--strict", str(t))


@nox.session
def code_quality(session):
    session.install("-r", "requirements_code_quality.txt")

    srcs = [
        _this_dir() / "src" / "py_openocd_client",
    ]
    tests = [
        _this_dir() / "tests_unit",
        _this_dir() / "tests_integration",
    ]
    utils = [
        _this_dir() / "make_release.py",
        _this_dir() / "tests_integration" / "build_openocd.py",
        _this_dir() / "tests_integration" / "openocd_version_info.py",
    ]
    noxfile = [_this_dir() / "noxfile.py"]

    make_edits = "-e" in session.posargs

    _run_isort(session, srcs + tests + utils + noxfile, make_edits)
    _run_black(session, srcs + tests + utils + noxfile, make_edits)
    _run_flake8(session, srcs + tests + utils + noxfile)
    _run_mypy(session, srcs + utils)


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"])
def tests_unit(session):
    session.install(".")
    session.install("pytest")
    session.run("python3", "-m", "pytest", "tests_unit/", "-vv", *session.posargs)


@nox.session
def tests_unit_coverage(session):
    # Install the package as editable (-e) so that the source files remain
    # within the current directory and the coverage picks them up.
    session.install("-e", ".")

    session.install("pytest", "coverage")
    session.run(
        "python3",
        "-m",
        "coverage",
        "run",
        "-m",
        "pytest",
        "tests_unit/",
        "-vv", 
        *session.posargs,
    )
    session.run("python3", "-m", "coverage", "xml")
    session.run("python3", "-m", "coverage", "html")

    # Require 100% coverage
    session.run("python3", "-m", "coverage", "report", "--fail-under", "100")


@nox.session(default=False)
def tests_integration(session):
    session.install(".")
    session.install("pytest")
    # Additional arguments --openocd-path and --openocd-version are required,
    # see tests_integration/conftest.py.
    session.run(
        "python3", "-m", "pytest", "tests_integration/", "-vv", *session.posargs
    )


@nox.session
def build_doc(session):
    session.install("-r", "requirements_doc.txt")
    session.chdir("doc")
    session.run(
        "python3",
        "-m",
        "sphinx",
        "--fail-on-warning",
        "--keep-going",
        ".",
        "_build/html",
    )
