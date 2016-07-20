# -*- coding: utf-8 -*-
from __future__ import division
import logging
from math import sqrt

from sqlalchemy.sql import text

from ..models.base import DBSession
from ..models.base import get_connection
from ..models.icf_result import Icf_Result

log = logging.getLogger(__name__)

"""
求出任意2个产品的相似度，然后用相近的用户进行推荐
"""

def _get_dataset():
    """
    生成一个巨大的用户数组
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
                if user_id not in dataset:
                    dataset[user_id] = {}
                if product_id not in dataset[user_id]:
                    dataset[user_id][product_id] = 1
                else:
                    dataset[user_id][product_id] += 1
        else:
            break
    return dataset


def _get_all_users():
    """
    生成一个巨大的用户数组
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct user_id from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    return sql_answer


# def similarity_score(dataset, person1, person2):
#     """Returns ratio Euclidean distance score of person1 and person2"""
#     both_viewed = {}		# To get both rated items by person1 and person2
#     for item in dataset[person1]:
#         if item in dataset[person2]:
#             both_viewed[item] = 1
#     # Conditions to check they both have an common rating items	
#     if len(both_viewed) == 0:
#         return 0
#     # Finding Euclidean distance 
#     sum_of_eclidean_distance = []	
#     for item in dataset[person1]:
#         if item in dataset[person2]:
#             sum_of_eclidean_distance.append(pow(dataset[person1][item] - dataset[person2][item], 2))
#             sum_of_eclidean_distance = sum(sum_of_eclidean_distance)
#     return 1/(1+sqrt(sum_of_eclidean_distance))


def pearson_correlation(dataset, person1, person2):
    if (person1 not in dataset) or (person2 not in dataset):
        return 0
    # To get both rated items
    both_rated = {}
    for item in dataset[person1]:
        if item in dataset[person2]:
            both_rated[item] = 1
    number_of_ratings = len(both_rated)		
    # Checking for number of ratings in common
    if number_of_ratings == 0:
        return 0
    # Add up all the preferences of each user
    person1_preferences_sum = sum([dataset[person1][item] for item in both_rated])
    person2_preferences_sum = sum([dataset[person2][item] for item in both_rated])
    # Sum up the squares of preferences of each user
    person1_square_preferences_sum = sum([pow(dataset[person1][item],2) for item in both_rated])
    person2_square_preferences_sum = sum([pow(dataset[person2][item],2) for item in both_rated])
    # Sum up the product value of both preferences for each item
    product_sum_of_both_users = sum([dataset[person1][item] * dataset[person2][item] for item in both_rated])
    # Calculate the pearson score
    numerator_value = product_sum_of_both_users - (person1_preferences_sum*person2_preferences_sum/number_of_ratings)
    denominator_value = sqrt((person1_square_preferences_sum - pow(person1_preferences_sum,2)/number_of_ratings) * (person2_square_preferences_sum -pow(person2_preferences_sum,2)/number_of_ratings))
    if denominator_value == 0:
        return 0
    else:
        r = numerator_value/denominator_value
        return r 


# def most_similar_users(person, number_of_users):
#     # returns the number_of_users (similar persons) for a given specific person.
#     scores = [(pearson_correlation(person,other_person), other_person) for other_person in dataset if  other_person != person ]
#     # Sort the similar persons so that highest scores person will appear at the first
#     scores.sort()
#     scores.reverse()
#     return scores[0:number_of_users]

# def user_reommendations(dataset, person):
#     # Gets recommendations for a person by using a weighted average of every other user's rankings
#     totals = {}
#     simSums = {}
#     rankings_list =[]
#     for other in dataset:
#         # don't compare me to myself
#         if other == person:
#             continue
#         sim = pearson_correlation(person,other)
#         if sim <=0: 
#             continue
#         for item in dataset[other]:
#             # only score movies i haven't seen yet
#             if item not in dataset[person] or dataset[person][item] == 0:
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
		

def _save_score(one_user, rel_user, score):
    if score > 0:
        print one_user, rel_user, score
        one_result = Icf_Result(
            user_id = one_user,
            rel_user_id = rel_user,
            score = score,
        )
        DBSession.add(one_result)


def do_icf_data():
    ## 获取每个用户全部购买产品
    all_data = _get_dataset()
    all_users = _get_all_users()
    for one_user_line in all_users:
        for rel_user_line in all_users:
            if one_user_line != rel_user_line:
                score = pearson_correlation(all_data, one_user_line[0], rel_user_line[0])
                _save_score(one_user_line[0], rel_user_line[0], score)
    
def job():
    do_icf_data()
    return

