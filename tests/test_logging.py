from __future__ import annotations

import sys
import textwrap

import pytest
from pony import orm
from pytask import cli
from pytask import ExitCode
from pytask_environment.database import Environment

# Can be removed with pytask v0.4.
try:
    from pytask import db
except ImportError:
    from _pytask.database_utils import db


@pytest.mark.end_to_end
def test_existence_of_python_executable_in_db(tmp_path, runner):
    """Test that the Python executable is stored in the database."""
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent("def task_dummy(): pass"))
    tmp_path.joinpath("pyproject.toml").write_text("[tool.pytask.ini_options]")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK

    with orm.db_session:
        python = Environment["python"]

        assert python.version == sys.version
        assert python.path == sys.executable

        orm.rollback()
        for entity in db.entities.values():
            orm.delete(e for e in entity)


@pytest.mark.end_to_end
def test_flow_when_python_version_has_changed(monkeypatch, tmp_path, runner):
    """Test the whole use-case.

    1. Run a simple task to cache the Python version and path.
    2. Pretend to use a different Python environment and decline to continue. Check that
       values in database have not been altered.
    3. Pretend that environment has changed, confirm to continue and check that new
       version and path are in database.

    """
    real_python_version = sys.version
    real_python_executable = sys.executable
    fake_version = (
        "2.7.8 | packaged by conda-forge | (default, Jul 31 2020, 01:53:57) "
        "[MSC v.1916 64 bit (AMD64)]"
    )

    tmp_path.joinpath("pyproject.toml").write_text("[tool.pytask.ini_options]")
    source = "def task_dummy(): pass"
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent(source))

    # Run without knowing the python version and without updating the environment.
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "Updating the information" in result.output

    # Run with a fake version and not updating the environment.
    monkeypatch.setattr("pytask_environment.logging.sys.version", fake_version)

    result = runner.invoke(cli)
    assert result.exit_code == ExitCode.FAILED

    with orm.db_session:
        python = Environment["python"]

    assert python.version == real_python_version
    assert python.path == real_python_executable

    # Run with a fake version and updating the environment.
    monkeypatch.setattr("pytask_environment.logging.sys.version", fake_version)
    monkeypatch.setattr("pytask_environment.logging.sys.executable", "new_path")

    result = runner.invoke(cli, ["--update-environment", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    with orm.db_session:
        python = Environment["python"]

        assert python.version == fake_version
        assert python.path == "new_path"

        orm.rollback()
        for entity in db.entities.values():
            orm.delete(e for e in entity)


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    ("check_python_version", "expected"), [("true", 1), ("false", 0)]
)
def test_python_version_changed(
    monkeypatch, tmp_path, runner, check_python_version, expected
):
    fake_version = (
        "2.7.8 | packaged by conda-forge | (default, Jul 31 2020, 01:53:57) "
        "[MSC v.1916 64 bit (AMD64)]"
    )
    tmp_path.joinpath("pyproject.toml").write_text(
        f"[tool.pytask.ini_options]\ncheck_python_version = {check_python_version}"
    )
    source = "def task_dummy(): pass"
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent(source))

    # Run without knowing the python version and without updating the environment.
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "Updating the information" in result.output

    # Run with a fake version and not updating the environment.
    monkeypatch.setattr("pytask_environment.logging.sys.version", fake_version)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == expected

    with orm.db_session:
        orm.rollback()
        for entity in db.entities.values():
            orm.delete(e for e in entity)


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    ("check_python_version", "expected"), [("true", 1), ("false", 0)]
)
def test_environment_changed(
    monkeypatch, tmp_path, runner, check_python_version, expected
):
    tmp_path.joinpath("pyproject.toml").write_text(
        f"[tool.pytask.ini_options]\ncheck_environment = {check_python_version}"
    )
    source = "def task_dummy(): pass"
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent(source))

    # Run without knowing the python version and without updating the environment.
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "Updating the information" in result.output

    # Run with a fake version and not updating the environment.
    monkeypatch.setattr("pytask_environment.logging.sys.executable", "new_path")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == expected

    with orm.db_session:
        orm.rollback()
        for entity in db.entities.values():
            orm.delete(e for e in entity)
