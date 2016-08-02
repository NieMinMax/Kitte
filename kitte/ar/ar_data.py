# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import
import logging
import math 

from sqlalchemy.sql import text

from ..models.base import get_connection
from ..models.ar_result import Ar_Result

log = logging.getLogger(__name__)

Is_Calc_AR = False

def _get_all_products():
    """
    获取全部商品
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct product_id from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    return sql_answer

def _get_order_count():
    """
    获取全部订单数
    """
    DBConnecion = get_connection()
    sql_str = text("""select count(distinct order_id) from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    return sql_answer

def _get_product_count():
    """
    获取每一个商品的下单数
    fixme:假设每个订单不会存在多条同商品记录
    """
    DBConnecion = get_connection()
    sql_str = text("""
    select product_id, count(product_id) from sorder_line group by product_id
    """)
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    return sql_answer
    
def _get_rel_count(one_product, rel_product):
    """
    获取2个商品的数量
    """
    all_products = (one_product, rel_product)
    DBConnecion = get_connection()
    sql_str = text(
        """
        select product_id, order_id from sorder_line 
        where product_id in :products
        order by order_id
        """)
    sql_answer = DBConnecion.execute(sql_str, products=all_products).fetchall()
    temp_map = {}
    for one_line in sql_answer:
        order_id = one_line[1]
        if order_id not in temp_map:
            temp_map[order_id] = {
                'origin':False,
                'rel':False
            }
        if one_line[0] == one_product:
            temp_map[order_id]['origin'] = True
        elif one_line[0] == rel_product:
            temp_map[order_id]['rel'] = True
    count = 0
    for one in temp_map:
        if temp_map[one]['origin'] and temp_map[one]['rel']:
            count += 1
    print("Scanning Done...")
    return count


def _save_rules(one_product, rel_product, support, db_session):
    """
    保存关联规则
    """
    print (one_product, rel_product, support)
    one_result = Ar_Result(
        product_id = one_product,
        rel_product_id = rel_product,
        support = support,
    )
    db_session.add(one_result)

    
def do_ar_data(settings, db_session):
    """
    暂在数据库内实现，不排除未来以内存方式实现
    """
    global Is_Calc_AR
    print (Is_Calc_AR)
    if Is_Calc_AR:
        log.info("It's calculating, skip...")
        return
    log.info("Start calculating...")
    Is_Calc_AR = True
    min_support = float(settings['min_support'])
    min_conf = float(settings['min_confidence'])
    print(min_support, min_conf)
    all_products = _get_all_products()
    order_total = _get_order_count()[0][0]
    product_support_results = _get_product_count()
    session_count = 0
    for (one_product, one_count) in product_support_results:
        # 满足支持度
        single_support = one_count / order_total
        if single_support >= min_support:
            for rel_product_line in all_products:
                if one_product != rel_product_line[0]:
                    couple_count = _get_rel_count(one_product, rel_product_line[0])
                    couple_support = couple_count / order_total
                    couple_conf = couple_count/one_count
                    if couple_support >= min_support and couple_conf >= min_conf:
                        save_rule(one_product, rel_product_line[0], couple_support, db_session)
                        session_count += 1
                        if session_count > 1000:
                            db_session.commit()
                            session_count = 0
    if session_count>0:
        db_session.commit()
    db_session.close()
    Is_Calc_AR = False
    return
                        

# def job(settings, dbmaker):
#     DB_SESSION = request.registry.dbmaker
#     db_session = DB_SESSION()
#     do_ar_data(settings, db_session)
#     return


        
