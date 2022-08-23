# coding: utf-8
# Author: crb
# Date: 2021/7/19 14:13

import sys
import os
import numpy as np
import random
from collections import defaultdict

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

def gen_feasible_configs(num_of_cores, core_top_k):
    num_app = len(core_top_k)
    top_k = len(core_top_k[0])
    for i in range(len(core_top_k)):
        for j in range(len(core_top_k[i])):
            if core_top_k[i][j] > num_of_cores - num_app + 1:
                if random.randint(1, 10) > 7:
                    core_top_k[i][j] = random.randint(1, (num_of_cores - num_app + 1))
                else:
                    core_top_k[i][j] = num_of_cores - num_app + 1

    def gen_side(tmp, k, n=1):
        """
        :param root: root node, first app node
        :param n: n_th in top_k
        :return:
        """
        if n == num_app:
            return [[]]

        for k in range(top_k):
            t1 = k * top_k ** (num_app - n - 1)
            t2 = top_k ** (num_app - 1) - (top_k - k - 1) * top_k ** (num_app - n - 1)
            delta2 = top_k ** (num_app - 1 - n)
            delta1 = top_k ** (num_app - n)
            for i in range(t1, t2, delta1):
                for j in range(i, i + delta2):
                    app_core = core_top_k[n][k]
                    feasible_core = num_of_cores - (num_app - len(tmp[j]) - 1) - sum(tmp[j])

                    if app_core > feasible_core:
                        tmp[j].append(feasible_core)
                    else:
                        tmp[j].append(app_core)

        gen_side(n=n + 1, tmp=tmp, k=k)

        return tmp

    all_feasible_config = []
    for j in range(top_k):
        tmp = [[core_top_k[0][j]] for _ in range(top_k ** (num_app - 1))]
        all_feasible_config.extend(gen_side(tmp, k=0))
    return all_feasible_config


# gen_feasible_configs(9,[[5, 0, 4], [7, 9, 3], [3, 4, 2]])

def get_top_k(arr, k, times):
    """
    :param arr:
    :param k:
    :return: top k
    """
    if times < 5 or random.randint(1, 10) > 8:
        arr_top_k_id = [random.randint(0, len(arr)) for _ in range(k)]
    else:
        arr_top_k_id = np.argsort(arr)[-k:]

    arr_top_k_id = [(i + 1) for i in list(arr_top_k_id)]

    return arr_top_k_id


def beam_search(num_of_cores, app_id, p_c_t, times, end_condition=30):
    """
    :param sum_core:
    :param app_id:
    :param end_condition:
    :return: max possibility colocation
    """
    core_action = {}.fromkeys(app_id)
    num_app = len(app_id)
    top_k = int(10 ** (np.log10(end_condition) / num_app))

    core_top_k = [get_top_k(p_c_t[app_id[i]], top_k, times) for i in range(num_app)]

    feasible_configs = gen_feasible_configs(num_of_cores=num_of_cores, core_top_k=core_top_k)
    sum_p_list = []
    for config in feasible_configs:
        config_p = [p_c_t[app_id[i]][config[i]] for i in range(num_app)]
        sum_p = sum(config_p)
        sum_p_list.append(sum_p)
    # print(sum_p_list)

    core_act = feasible_configs[np.argmax(sum_p_list)]
    for i in range(num_app):
        core_action[app_id[i]] = core_act[i]

    return core_action


def get_key(dict, value):
    for k, v in dict.items():
        if v == value:
            return k


def get_llc_bandwith_config():
    nof_llc = 10
    nof_band = 10
    llc_config = []
    mb_config = []
    for i in range(1, nof_llc + 1):
        for j in range(i, nof_llc + 1):
            llc_config.append([i, j])
    for i in range(1, nof_band + 1):
        mb_config.append(i)
    return llc_config, mb_config


def list_duplicates(choose_arm_dict, app_id):
    """
    :param seq:
    :return: multi bandit choose
    """
    core, llc, mb = [], [], []
    core_config = {}.fromkeys(app_id, [])
    llc_config = {}.fromkeys(app_id, [])
    mb_config = {}.fromkeys(app_id, [])
    for i in range(len(choose_arm_dict)):
        core.append(choose_arm_dict[i][0])
        llc.append(choose_arm_dict[i][1])
        mb.append(choose_arm_dict[i][2])

    for k in app_id:
        core_config[k] = [core_config[k] for core_config in core]
        llc_config[k] = [llc_config[k] for llc_config in llc]
        mb_config[k] = [mb_config[k] for mb_config in mb]

    def choose_id(seq, flag=None):
        tally = defaultdict(list)
        for i, item in enumerate(seq):
            tally[item].append(i)
        choose_l = []
        for key, locs in tally.items():
            if len(locs) > 1:
                choose_l.append(key)
        if choose_l == []:
            if flag == "cpu":
                choose_key = seq[0]
            else:
                choose_key = seq[random.randint(0, len(seq) - 1)]
            return choose_key
        else:
            tmp = 1
            for k in choose_l:
                v = len(tally[k])
                if v > tmp:
                    choose_key = k
                    tmp = v
        if tmp == 1:
            if flag == "cpu":
                choose_key = choose_l[0]
            else:
                choose_key = random.choice(choose_l)

        return choose_key

    for m, val in core_config.items():
        core_config[m] = choose_id(val, "cpu")
    for m, val in llc_config.items():
        llc_config[m] = choose_id(val)
    for m, val in mb_config.items():
        mb_config[m] = choose_id(val)

    choose_arm = [core_config, llc_config, mb_config]
    return choose_arm
