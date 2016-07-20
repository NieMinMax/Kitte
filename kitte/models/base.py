# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from sqlalchemy import create_engine
import pyramid.threadlocal

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

## As a convenience feature, the declarative_base() sets a default constructor on classes which takes keyword arguments, and assigns them to the named attributes:

def get_connection():
    """
    new connection for raw text query
    """
    DBConnection = DBSession.connection()
    return DBConnection

