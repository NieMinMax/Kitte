# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import tensorflow as tf
import numpy as np

import logging
from math import sqrt

from sqlalchemy.sql import text

from ..models.base import DBSession
from ..models.base import get_connection
from ..models.ucf_result import Ucf_Result

log = logging.getLogger(__name__)

DATA_PATH = "./model.ckpt"

class Autoencoder(object):

    def __init__(self, feature_lens):

        self.feature_lens = feature_lens
        self.hidden_lens = feature_lens/2
        self.learning_rate = 0.01
        self.saver = tf.train.Saver()

        self.X = tf.placeholder("float", [self.feature_lens])

        encoder_h = tf.Variable(tf.random_normal([self.feature_lens])),
        encoder_b = tf.Variable(tf.random_normal([self.hidden_lens])),
        
        self.hidden_layer = tf.nn.sigmoid(
            tf.add(tf.matmul(self.X, encoder_h), encoder_b))

        decoder_h = tf.transpose(encoder_h)
        decoder_b = encoder_b
        self.final_layer = tf.nn.sigmoid(
                tf.add(tf.matmul(self.hidden_layer, decoder_h), decoder_b))

        # Define loss and optimizer, minimize the squared error
        self.cost = tf.reduce_mean(
            tf.pow(self.X - self.final_layer, 2))
        self.optimizer = tf.train.GradientDescentOptimizer(learning_rate).minimize(self.cost)
        init = tf.initialize_all_variables()
        # Launch the session
        self.sess = tf.Session()
        self.sess.run(init)
        return 

    def train(self, train_data):
        opt, cost = self.sess.run((self.optimizer, self.cost), 
                                  feed_dict={self.X: train_data})
        log.info(cost)
        return

    def _del_(self):
        saver.save(self.sess, DATA_PATH)
        self.session.close()


def _get_all_products():
    """
    获取全部商品 
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct product_id from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    all_products = [one_product[0] for one_product in sql_answer]
    return all_products


def _get_all_users():
    """
    获取全部用户
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct user_id from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    all_users = [one_user[0] for one_user in sql_answer]
    return all_users


def _get_one_user_data(user_id):
    """
    获取某个用户数据
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct product_id from sorder_line where user_id=:user_id""")
    sql_answer = DBConnecion.execute(sql_str, user_id).fetchall()
    user_products = [one_product[0] for one_product in sql_answer]
    return user_products


def format_data(all_products, user_products):
    """
    格式化产品数据
    """
    fdata = []
    for one_product in all_products:
        if one_product in user_products:
            fdata += [1]
        else:
            fdata += [0]
    return

            
def do_ae_model():
    ## 获取全部购买商品
    all_products = _get_all_products()
    ## 构建模型
    ae = Autoencoder(len(all_products))
    all_users = get_all_users()
    train_data = []
    for one_user in all_users():
        user_products = _get_one_user_data(user_id)
        ## 如何用稀疏数据表示
        fdata = format_data(all_products, user_products)
        train_data += [fdata]
        if len(train_data)>=1000:
            ae.train(train_data)
            train_data = []
    return 
    

def job():
    do_ae_model()
    return

