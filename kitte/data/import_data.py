# -*- coding: utf-8 -*-
import logging
import multiprocessing
import psycopg2

import pyramid.threadlocal
from sqlalchemy.sql import text

from ..models.base import DBSession
from ..models.order_line import SOrderLine

log = logging.getLogger(__name__)

Is_Importing = False

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
    
def _gen_final_data(group_datas, db_session):
    for one_data in group_datas:
        order_line = SOrderLine(
            order_id = one_data[0],
            product_id = one_data[1],
            user_id = one_data[2],
            create_date = one_data[3],
            )
        db_session.add(order_line)
    db_session.commit()
    return True

def _import_data(origin_connection, origin_db_sql, db_session):
    page_count = 0
    while True:
        one_group_data = _get_origin_data(origin_connection,
                                          origin_db_sql,
                                          page_count)
        if one_group_data and one_group_data[0][0] and one_group_data[0][1] and one_group_data[0][2]:
            _gen_final_data(one_group_data, db_session)
            page_count += 1
        else:
            log.info("Import Ending...")
            break

def import_data(settings, db_session):
    global Is_Importing
    if Is_Importing:
        log.info("It's Importing, skip...")
        return
    log.info("Start Ending...")
    Is_Importing = True
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
    db_session.query(SOrderLine).filter().delete()
    db_session.commit()
    p = multiprocessing.Process(target=_import_data, args=(origin_connection, origin_db_sql, db_session))
    p.start()
    p.join()
    db_session.close()
    Is_Importing = False
    return

# def job():
#     maker = request.registry.dbmaker
#     db_session = maker()
#     import_data(settings, db_session)
#     return
