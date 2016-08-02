# -*- coding: utf-8 -*-
from pyramid.view import view_config

from data.import_data import import_data
from ar.ar_data import do_ar_data
from cf.ucf_data import do_ucf_data
from cf.icf_data import do_icf_data
from nn.ae import do_ae_model

from models.base import DBSession
from models.ar_result import Ar_Result
from models.icf_result import Icf_Result
from models.ucf_result import Ucf_Result


RESULT_LEN = 20


@view_config(route_name='home', renderer='templates/kitte.pt')
def default_view(request):
    return {'project': 'Kitte'}

@view_config(route_name='import_data', renderer='string')
def do_import_data(request):
    settings = request.registry.settings
    dbmaker = request.registry.dbmaker
    db_session = dbmaker()
    import_data(settings, db_session)
    return u'Importing Data...'

@view_config(route_name='do_ar', renderer='string')
def do_import_ar(request):
    settings = request.registry.settings
    maker = request.registry.dbmaker
    db_session = maker()
    do_ar_data(settings, db_session)
    return u'Calculating AR...'

@view_config(route_name='get_ar', renderer='json')
def do_get_ar(request):
    product_ids = request.params.getall('product')
    result_ids = []
    if product_ids:
        all_products = DBSession.query(Ar_Result).filterx(Ar_Result.product_id.in_(product_ids)).order_by(Ar_Result.support.desc()).limit(RESULT_LEN).all()
        result_ids = [one.rel_product_id for one in all_products]
    return result_ids

@view_config(route_name='do_ucf', renderer='string')
def do_import_ucf(request):
    maker = request.registry.dbmaker
    db_session = maker()
    do_ucf_data(db_session)
    return u'start calculating ucf...'

@view_config(route_name='get_ucf', renderer='json')
def do_get_ucf(request):
    product_ids = request.params.getall('product')
    result_ids = []
    if product_ids:
        all_products = DBSession.query(Ucf_Result).filter(Ucf_Result.product_id.in_(product_ids)).order_by(Ucf_Result.score.desc()).limit(RESULT_LEN).all()
        result_ids = [one.rel_product_id for one in all_products]
    return result_ids

@view_config(route_name='do_icf', renderer='string')
def do_import_icf(request):
    maker = request.registry.dbmaker
    db_session = maker()
    do_icf_data(db_session)
    return u'start calculating icf...'


@view_config(route_name='get_icf', renderer='json')
def do_get_icf(request):
    user_ids = request.params.getall('user')
    result_ids = []
    if user_ids:
        all_users = DBSession.query(Icf_Result).filter(Icf_Result.user_id.in_(user_ids)).order_by(Icf_Result.score.desc()).limit(RESULT_LEN).all()
        result_ids = [one.rel_user_id for one in all_users]
    return result_ids

@view_config(route_name='do_ae', renderer='string')
def do_start_ae_model(request):
    do_ae_model()
    return u'start building ae Model...'

@view_config(route_name='get_ae', renderer='json')
def do_get_ae(request):
    user_id = request.matchdict['user']
    return 


