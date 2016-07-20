# -*- coding: utf-8 -*-
from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    DateTime,
    String,
    Enum,
    )

from base import Base

class SOrderLine(Base):
    __tablename__ = 'sorder_line'
    id = Column(Integer, primary_key=True)
    order_id = Column(String)
    product_id = Column(String)
    user_id = Column(String)
    create_date = Column(DateTime)
    
    # like_type = Column(Enum(u'factory',
    #                         u'brand',
    #                         u'shop',
    #                         u'product',
    #                         name='like_type'))
    # like_code = Column(String)
    # remote_ip = Column(String)
    # local_ip = Column(String)

# class EShopVisit(Base):
#     __tablename__ = 'eshop_visit'
#     id = Column(Integer, primary_key=True)
#     factory_code = Column(String)
#     visit_type = Column(Enum(u'factory',
#                              u'brand',
#                              u'shop',
#                              u'product',
#                              name='visit_type'))
#     visit_code = Column(String)
#     remote_ip = Column(String)
#     local_ip = Column(String)
#     start_time = Column(DateTime)
#     ## end_time = Column(DateTime)

# Index('company_code_index', EShopVisit.factory_code)

