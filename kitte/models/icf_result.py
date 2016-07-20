# -*- coding: utf-8 -*-
from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Float
    )

from base import Base

class Icf_Result(Base):
    __tablename__ = 'icf_result'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    rel_user_id = Column(String)
    score = Column(Float)
