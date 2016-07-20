# -*- coding: utf-8 -*-
from __future__ import division
import logging
from math import sqrt

from sqlalchemy.sql import text

from ..models.base import DBSession
from ..models.base import get_connection
from ..models.ucf_result import Ucf_Result

log = logging.getLogger(__name__)

"""
求出任意2个用户的相似度，然后用相近的产品推荐
"""

def _get_dataset():
    """
    生成一个巨大的用户数组，每个用户对每个商品的购买次数
    """
    DBConnecion = get_connection()
    page_count = 0
    dataset = {}
    while True:
        sql_str = text(
            """
            select user_id, product_id from sorder_line limit 5000 offset :skip_line
            """)
        sql_answer = DBConnecion.execute(sql_str, skip_line = page_count*5000,
                                     ).fetchall()
        if sql_answer and sql_answer[0] and sql_answer[1] and sql_answer[2]:
            page_count += 1
            for one_line in sql_answer:
                product_id = one_line[1]
                user_id = one_line[0]
                if product_id not in dataset:
                    dataset[product_id] = {}
                if user_id not in dataset[product_id]:
                    dataset[product_id][user_id] = 1
                else:
                    dataset[product_id][user_id] += 1
        else:
            break
    return dataset


def _get_all_items():
    """
    生成一个巨大的用户数组
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct product_id from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    return sql_answer


# def similarity_score(dataset, item1, item2):
#     """Returns ratio Euclidean distance score of item1 and item2"""
#     both_viewed = {}		# To get both rated items by item1 and item2
#     for person in dataset[item1]:
#         if person in dataset[item2]:
#             both_viewed[person] = 1
#     # Conditions to check they both have an common rating items	
#     if len(both_viewed) == 0:
#         return 0
#     # Finding Euclidean distance 
#     sum_of_eclidean_distance = []	
#     for person in dataset[item1]:
#         if person in dataset[item2]:
#             sum_of_eclidean_distance.append(pow(dataset[item1][person] - dataset[item2][person], 2))
#             sum_of_eclidean_distance = sum(sum_of_eclidean_distance)
#     return 1/(1+sqrt(sum_of_eclidean_distance))


def pearson_correlation(dataset, item1, item2):
    if (item1 not in dataset) or (item2 not in dataset):
        return 0
    # To get both rated items
    both_rated = {}
    for person in dataset[item1]:
        if person in dataset[item2]:
            both_rated[person] = 1
    number_of_ratings = len(both_rated)		
    # Checking for number of ratings in common
    if number_of_ratings == 0:
        return 0
    # Add up all the preferences of each user
    item1_preferences_sum = sum([dataset[item1][person] for person in both_rated])
    item2_preferences_sum = sum([dataset[item2][person] for person in both_rated])
    # Sum up the squares of preferences of each user
    item1_square_preferences_sum = sum([pow(dataset[item1][person],2) for person in both_rated])
    item2_square_preferences_sum = sum([pow(dataset[item2][person],2) for person in both_rated])
    # Sum up the product value of both preferences for each item
    product_sum_of_both_users = sum([dataset[item1][person] * dataset[item2][person] for person in both_rated])
    # Calculate the pearson score
    numerator_value = product_sum_of_both_users - (item1_preferences_sum*item2_preferences_sum/number_of_ratings)
    denominator_value = sqrt((item1_square_preferences_sum - pow(item1_preferences_sum,2)/number_of_ratings) * (item2_square_preferences_sum -pow(item2_preferences_sum,2)/number_of_ratings))
    if denominator_value == 0:
        return 0
    else:
        r = numerator_value/denominator_value
        return r 


# def most_similar_users(item, number_of_users):
#     # returns the number_of_users (similar items) for a given specific item.
#     scores = [(pearson_correlation(item,other_item), other_item) for other_item in dataset if  other_item != item ]
#     # Sort the similar items so that highest scores item will appear at the first
#     scores.sort()
#     scores.reverse()
#     return scores[0:number_of_users]

# def user_reommendations(dataset, item):
#     # Gets recommendations for a item by using a weighted average of every other user's rankings
#     totals = {}
#     simSums = {}
#     rankings_list =[]
#     for other in dataset:
#         # don't compare me to myself
#         if other == item:
#             continue
#         sim = pearson_correlation(item,other)
#         if sim <=0: 
#             continue
#         for item in dataset[other]:
#             # only score movies i haven't seen yet
#             if item not in dataset[item] or dataset[item][item] == 0:
#                 # Similrity * score
#                 totals.setdefault(item, 0)
#                 totals[item] += dataset[other][item]* sim
#                 # sum of similarities
#                 simSums.setdefault(item, 0)
#                 simSums[item]+= sim
#                 # Create the normalized list
#     rankings = [(total/simSums[item], item) for item, total in totals.items()]
#     rankings.sort()
#     rankings.reverse()
#     # returns the recommended items
#     recommendataions_list = [recommend_item for score,recommend_item in rankings]
#     return recommendataions_list
		

def _save_score(one_product, rel_product, score):
    if score > 0:
        print one_product, rel_product, score
        one_result = Ucf_Result(
            product_id = one_product,
            rel_product_id = rel_product,
            score = score,
        )
        DBSession.add(one_result)

def do_ucf_data():
    ## 获取每个用户全部购买产品
    all_data = _get_dataset()
    all_items = _get_all_items()
    for one_item_line in all_items:
        for rel_item_line in all_items:
            if one_item_line != rel_item_line:
                score = pearson_correlation(all_data, one_item_line[0], rel_item_line[0])
                _save_score(one_item_line[0], rel_item_line[0], score)
    

def job():
    do_ucf_data()
    return

