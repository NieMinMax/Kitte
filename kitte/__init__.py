# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid_rpc.xmlrpc import XMLRPCRenderer

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

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


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    config = Configurator(settings=settings)
    ## db session
    config.registry.dbmaker = sessionmaker(bind=engine)
    
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

    # scheduler = BackgroundScheduler()
    ## AR
    # product_trigger = IntervalTrigger(seconds=10000)
    # scheduler.add_job(
    #     apicron.product.job,
    #     product_trigger,
    #     [(settings, config.registry.shop_redis_pool)]
    # )
    # scheduler.start()
    
    ## route
    config.add_route('home', '/')
    config.add_route('import_data', '/do/import')

    config.add_route('do_ar', '/do/ar')
    config.add_route('get_ar', '/get/ar')

    config.add_route('do_ucf', '/do/ucf')
    config.add_route('get_ucf', '/get/ucf')    

    config.add_route('do_icf', '/do/icf')
    config.add_route('get_icf', '/get/icf')    

    config.add_route('do_ae', '/do/ae')
    config.add_route('get_ae', '/get/ae')    

    
    # ## propogate
    # config.add_route('propagate_product', '/api/product/getcooperatedproduct_popergate/')
    config.scan()
    return config.make_wsgi_app()
