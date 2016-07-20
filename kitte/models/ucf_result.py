# -*- coding: utf-8 -*-
from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Float
    )

from base import Base

class Ucf_Result(Base):
    __tablename__ = 'ucf_result'
    id = Column(Integer, primary_key=True)
    product_id = Column(String)
    rel_product_id = Column(String)
    score = Column(Float)
