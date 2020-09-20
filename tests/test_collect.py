import os
import sys
import textwrap

import pytest
from _pytask.database import create_database
from pony import orm
from pytask import cli
from pytask_environment.database import Environment


@pytest.mark.end_to_end
def test_existence_of_python_executable_in_db(tmp_path, runner):
    """Test that the Python executable is stored in the database."""
    source = """
    import pytask

    def task_dummy():
        pass
    """
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent(source))

    os.chdir(tmp_path)
    result = runner.invoke(cli)

    assert result.exit_code == 0

    orm.db_session.__enter__()

    create_database(
        "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
    )

    python = Environment["python"]
    assert python.version == sys.version
    assert python.path == sys.executable

    orm.db_session.__exit__()


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info[:2] == (3, 6),
    reason="Error on Windows with Python 3.6",
)
@pytest.mark.end_to_end
def test_prompt_when_python_version_has_changed(monkeypatch, tmp_path, runner):
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

    source = """
    import pytask

    def task_dummy():
        pass
    """
    task_path = tmp_path.joinpath("task_dummy.py")
    task_path.write_text(textwrap.dedent(source))

    os.chdir(tmp_path)
    result = runner.invoke(cli)

    assert result.exit_code == 0

    monkeypatch.setattr("pytask_environment.collect.sys.version", fake_version)

    result = runner.invoke(cli, input="N")
    assert result.exit_code == 3

    orm.db_session.__enter__()

    create_database(
        "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
    )

    python = Environment["python"]
    assert python.version == real_python_version
    assert python.path == real_python_executable

    orm.db_session.__exit__()

    monkeypatch.setattr("pytask_environment.collect.sys.version", fake_version)
    monkeypatch.setattr("pytask_environment.collect.sys.executable", "new_path")

    result = runner.invoke(cli, input="y")
    assert result.exit_code == 0

    orm.db_session.__enter__()

    create_database(
        "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
    )

    python = Environment["python"]
    assert python.version == fake_version
    assert python.path == "new_path"

    orm.db_session.__exit__()
