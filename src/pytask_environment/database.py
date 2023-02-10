"""This module contains everything related to the database."""
from __future__ import annotations

from pony import orm

try:
    from pytask import db
except ImportError:
    from _pytask.database import db


class Environment(db.Entity):
    """Collects all information of the environment which should be checked."""

    name = orm.PrimaryKey(str)
    version = orm.Required(str)
    path = orm.Required(str)
