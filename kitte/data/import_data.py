# -*- coding: utf-8 -*-
import logging
import psycopg2

import pyramid.threadlocal
from sqlalchemy.sql import text

from ..models.base import DBSession
from ..models.order_line import SOrderLine

log = logging.getLogger(__name__)

def _get_origin_connection(host, port, dbname, user, passwd):
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=dbname,
        user=user,
        password=passwd)
    return conn

def _get_origin_data(conn, sql_str, page_count):
    cur = conn.cursor()
    do_sql_str = sql_str + " limit 5000 offset " + str(page_count*5000)
    cur.execute(do_sql_str)
    result = cur.fetchall()
    cur.close()
    return result
    
def _gen_final_data(group_datas):
    for one_data in group_datas:
        order_line = SOrderLine(
            order_id = one_data[0],
            product_id = one_data[1],
            user_id = one_data[2],
            create_date = one_data[3],
            )
        DBSession.add(order_line)
    return True

def import_data(settings):
    origin_db_host = settings['origin_db_host']
    origin_db_port = settings['origin_db_port']
    origin_db_name = settings['origin_db_name']
    origin_db_user = settings['origin_db_user']
    origin_db_passwd = settings['origin_db_passwd']
    origin_db_sql = settings['origin_db_sql']
    origin_connection = _get_origin_connection(
        origin_db_host,
        origin_db_port,
        origin_db_name,
        origin_db_user,
        origin_db_passwd)
    page_count = 0
    DBSession.query(SOrderLine).filter().delete()
    while True:
        one_group_data = _get_origin_data(origin_connection,
                                          origin_db_sql,
                                          page_count)
        if one_group_data and one_group_data[0][0] and one_group_data[0][1] and one_group_data[0][2]:
            _gen_final_data(one_group_data)
            page_count += 1
        else:
            break

def job(settings):
    import_data(settings)
    return
