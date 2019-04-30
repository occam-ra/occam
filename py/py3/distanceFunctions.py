# coding=utf-8
# Copyright © 1990 The Portland State University OCCAM Project Team
# [This program is licensed under the GPL version 3 or later.]
# Please see the file LICENSE in the source
# distribution of this software for license terms.

import math
import sys


def zipwise_fold(base, fold, proj, ls):
    res = base
    d0 = ls[0]["sparse_table"]
    d1 = ls[1]["sparse_table"]
    for (key0, value0) in list(d0.items()):

        if math.isnan(value0):
            print(
                f"ERROR: (nan) value in fit table for file '{ls[0]['filename']}' with model {ls[0]['name']}"
            )
            sys.exit(1)
        if math.isinf(value0):
            print(
                f"ERROR: (inf) value in fit table for file '{ls[0]['filename']}' with model {ls[0]['name']}"
            )
            sys.exit(1)
        if key0 in d1:
            res = fold(res, proj(value0, d1[key0]))
        else:
            res = fold(res, proj(value0, 0.0))
    for (key1, value1) in list(d1.items()):
        if math.isnan(value1):
            print(
                f"ERROR: (nan) value in fit table for file '{ls[1]['filename']}' with model {ls[1]['name']}"
            )
            sys.exit(1)
        if math.isinf(value1):
            print(
                f"ERROR: (inf) value in fit table for file '{ls[1]['filename']}' with model {ls[1]['name']}"
            )
            sys.exit(1)
        if key1 not in d0:
            res = fold(res, proj(0.0, value1))
    return res


def zipwise_sum(proj, ls):
    return zipwise_fold(0, lambda x, y: x + y, proj, ls)


def zipwise_max(proj, ls):
    return zipwise_fold(0, lambda x, y: max(x, y), proj, ls)


def absolute_dist(compare_order):
    return zipwise_sum(lambda x, y: abs(x - y), compare_order)


def euclidean_dist(compare_order):
    return math.sqrt(zipwise_sum(lambda x, y: (x - y) ** 2, compare_order))


def bhattacharya_coeff(compare_order):
    return zipwise_sum(lambda x, y: math.sqrt(x * y), compare_order)


def hellinger_dist(compare_order):
    return math.sqrt(1 - bhattacharya_coeff(compare_order))


PROB_MIN = 1e-36


def kl_component_sum(x, y):
    return 0 if (x < PROB_MIN or y < PROB_MIN) else x * math.log(x / y)


def kl_dist(compare_order):
    return zipwise_sum(kl_component_sum, compare_order) / math.log(2)


def max_dist(compare_order):
    return zipwise_max(lambda x, y: abs(x - y), compare_order)


distanceMetrics = {
    "Absolute dist": absolute_dist,
    "Euclidean dist": euclidean_dist,
    "Hellinger dist": hellinger_dist,
    "Kullback-Leibler dist": kl_dist,
    "Maximum dist": max_dist,
}


def compute_distance_metric(k, compare_order):
    return distanceMetrics[k](compare_order)
