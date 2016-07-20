# -*- coding: utf-8 -*-
from sqlalchemy import (
    Column,
    Index,
    Integer,
    Float,
    Text,
    String,
    )

from base import Base

class Ar_Result(Base):
    __tablename__ = 'ar_result'
    id = Column(Integer, primary_key=True)
    product_id = Column(String)
    rel_product_id = Column(String)
    support = Column(Float)
