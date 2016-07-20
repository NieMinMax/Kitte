# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid_rpc.xmlrpc import XMLRPCRenderer

from sqlalchemy import engine_from_config

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from models.base import (
    DBSession,
    Base,
    )

from models.order_line import (
    SOrderLine,
    )
from models.ar_result import (
    Ar_Result,
    )
from models.ucf_result import (
    Ucf_Result,
    )
from models.icf_result import (
    Icf_Result,
    )

# import apicron.tracking
# import apicron.product
# import apicron.stock
# import apicron.oe_get_dl
# import apicron.oe_save_dl
# import apicron.shop_save_dl
# import gen_data


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    config = Configurator(settings=settings)

    ## xmlrpc
    # config.include('pyramid_rpc.xmlrpc')
    # config.add_renderer('apixmlrpc', XMLRPCRenderer(allow_none=True))
    # config.add_xmlrpc_endpoint('api',
    #                            '/api/xmlrpc/page_oe_sync.php',
    #                            default_renderer='apixmlrpc'
    # )
    
    ## 页面展示
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)

    ## request中加入redis设置
    # config.registry.erp_redis_pool = redis.ConnectionPool(
    #     host=settings['erp_redis_host'],
    #     port=settings['erp_redis_port'],
    #     db='',
    # )
    # config.registry.shop_redis_pool = redis.ConnectionPool(
    #     host=settings['shop_redis_host'],
    #     port=settings['shop_redis_port'],
    #     password=settings['shop_redis_pwd'],
    #     db=''
    # )

    scheduler = BackgroundScheduler()

    # regen_data_trigger = IntervalTrigger(seconds=settings['regen_interval'])
    # scheduler.add_job(
    #     recommend.gen_data.job,
    #     regen_data_trigger,
    #     [settings]
    # )

    
    ## 获取物流单号
    # get_dl_trigger = IntervalTrigger(seconds=2000)
    # scheduler.add_job(
    #     apicron.oe_get_dl.job,
    #     get_dl_trigger,
    #     [config.registry.erp_redis_pool]
    # )
    ## 保存物流单号
    # oe_save_dl_trigger = IntervalTrigger(seconds=500)
    # scheduler.add_job(
    #     apicron.oe_save_dl.job,
    #     oe_save_dl_trigger,
    #     [config.registry.erp_redis_pool]
    # )
    ## 保存物流单号至Shop
    # shop_save_dl_trigger = IntervalTrigger(seconds=500)
    # scheduler.add_job(
    #     apicron.shop_save_dl.job,
    #     shop_save_dl_trigger,
    #     [config.registry.erp_redis_pool, config.registry.shop_redis_pool]
    # )
    
    ## 物流轨迹
    # tracking_trigger = IntervalTrigger(seconds=2000)
    # scheduler.add_job(
    #     apicron.tracking.job,
    #     tracking_trigger,
    #     [config.registry.erp_redis_pool]
    # )

    ## 产品上传
    # product_trigger = IntervalTrigger(seconds=10000)
    # scheduler.add_job(
    #     apicron.product.job,
    #     product_trigger,
    #     [(settings, config.registry.shop_redis_pool)]
    # )
    # ## 库存同步
    # stock_trigger = IntervalTrigger(seconds=10000)
    # scheduler.add_job(
    #     apicron.stock.job,
    #     stock_trigger,
    #     [(settings, config.registry.shop_redis_pool)]
    # )
    scheduler.start()
    
    ## route
    config.add_route('home', '/')
    config.add_route('import_data', '/do/import')

    config.add_route('do_ar', '/do/ar')
    config.add_route('get_ar', '/get/rel')

    config.add_route('do_ucf', '/do/ucf')
    # config.add_route('get_ar', '/get/rel')    

    config.add_route('do_icf', '/do/iycf')
    # config.add_route('get_ar', '/get/rel')    

    
    # config.add_route('tracking', '/tracking/{dl_sn}')
    # ## propogate
    # config.add_route('propagate_product', '/api/product/getcooperatedproduct_popergate/')
    # config.add_route('propagate_order', '/api/orderline/getrebateorderlines_popergate/')    
    # config.add_route('propagate_partner', '/api/customer/getpartnerinfo_popergate/')
    
    config.scan()
    return config.make_wsgi_app()
