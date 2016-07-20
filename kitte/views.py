# -*- coding: utf-8 -*-
from pyramid.view import view_config

from data.import_data import import_data
from ar.ar_data import do_ar_data
from cf.ucf_data import do_ucf_data
from cf.icf_data import do_icf_data

@view_config(route_name='home', renderer='templates/kitte.pt')
def my_view(request):
    return {'project': 'Kitte'}


@view_config(route_name='import_data', renderer='string')
def do_import_data(request):
    settings = request.registry.settings
    import_data(settings)
    return u'start importing...'

@view_config(route_name='do_ar', renderer='string')
def do_import_ar(request):
    settings = request.registry.settings
    do_ar_data(settings)
    return u'start calculating ar...'


@view_config(route_name='get_ar', renderer='json')
def do_get_ar(request):
    product_id = request.matchdict['product']
    all_products = DBSession.query(Ar_Result).filter_by(product_id=product)
    return all_products


@view_config(route_name='do_ucf', renderer='string')
def do_import_ucf(request):
    do_ucf_data()
    return u'start calculating ucf...'



@view_config(route_name='do_icf', renderer='string')
def do_import_icf(request):
    do_icf_data()
    return u'start calculating icf...'
