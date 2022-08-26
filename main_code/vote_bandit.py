# coding: utf-8
# Author: crb
# Date: 2021/7/17 20:53
import csv
import logging
import time

import numpy as np


from get_arm import bin_search, get_llc_bandwith_config, list_duplicates
from run_and_get_config import gen_config, gen_init_config, LC_APP_NAMES, get_now_ipc, stop_the_current_colocation, run_be_benchmark,run_lc_benchmark
from OLUCB import OLLinUCB



def train_success(nof_counters,colocation_list,load_list,alpha,rounds,context_flag=1,F=60):
    """
    :param nof_counters: Number of selected performance counters for providing contexts
    :param colocation_list: The coming colocations
    :param load_list: the loads of LC jobs
    :param alpha:  Explore-exploit parameter
    :param rounds: The Allowed Sampling Times For a Colocation
    :param context_flag: X defaults to 1, indicating the complete OLPart.
    :param F: the frequency of costructing a new version of bandits
     If it is set to a value other than 1, it is the OLPart without context
    :return:
    """

    init_alg = "fair"

    nof_colocation = len(colocation_list)
    # number of bandit versions
    mab_num = 3
    mab_1 = OLLinUCB(ndims=nof_counters, alpha=alpha, app_id = colocation_list[0],context_flag=context_flag)
    mab_2, mab_3 = 0, 0
    mab_list = [mab_1, mab_2, mab_3]
    mab_count = 1
    tmp_cumulative_reward, tmp_G = [[] for _ in range(mab_num)], [0 for _ in range(mab_num)]



    for col_items in range(nof_colocation):
        job_id = colocation_list[col_items]

        lc_job, be_job = [], []
        for i in job_id:
            if i in LC_APP_NAMES:
                lc_job.append(i)
            else:
                be_job.append(i)



        chose_arm_storage = []
        reward_arms = []

        # Offer the equally partitioning scheme in the initial
        core_list, llc_config, mb_config, chosen_arms = gen_init_config(job_id, llc_arm_orders,
                                                                        alg=init_alg)

        # run the colocations in order
        run_be_benchmark(be_job,core_list[len(lc_job):])
        load = load_list[col_items]
        for i in range(rounds):
            if rounds % F == 0:
                if mab_count < mab_num:
                    mab_list[mab_count] = OLLinUCB(nof_counters, alpha, colocation_list[col_items],context_flag=context_flag)
                    mab_count += 1
                else:
                    mab_count = 1
                    mab_list[0] = OLLinUCB(nof_counters, alpha, colocation_list[col_items],context_flag=context_flag)


            if i == 0:
                context, another_context, reward, p95_list = get_now_ipc(lc_job, be_job,load,
                                                                         performamce_counters)
                mab_1.add_del_job(job_id)

                chose_arm_storage.append([core_list, llc_config, mb_config])
                reward_arms, chosen_arms, tmp_cumulative_reward[0], tmp_G[0] = onlineEvaluate(mab_1, reward,
                                                                                              reward_arms, chosen_arms,
                                                                                              tmp_cumulative_reward[0],
                                                                                              context, another_context,
                                                                                              tmp_G[0], i)


            else:
                tmp_chosen_arms = []
                for ii in range(len(mab_list)):
                    if mab_list[ii] != 0:
                        mab_list[ii].add_del_job(job_id)
                        reward_arms_1, chosen_arms_1, tmp_cumulative_reward[ii], tmp_G[ii] = onlineEvaluate(
                            mab_list[ii], reward,
                            reward_arms, chosen_arms,
                            tmp_cumulative_reward[ii],
                            context,
                            another_context,
                            tmp_G[ii], i)
                        tmp_chosen_arms.append(chosen_arms_1)

                chosen_arms = list_duplicates(tmp_chosen_arms, job_id)
                reward_arms = reward_arms_1

                core_list, llc_config, mb_config = gen_config(job_id, chosen_arms, llc_arm_orders,
                                                              mb_arm_orders)
                time.sleep(1)
                context, another_context, reward, p95_list = get_now_ipc(lc_job, be_job,load,
                                                                         performamce_counters)
                chose_arm_storage.append([core_list, llc_config, mb_config])

            if reward > 0:
                p95_list.extend([reward, i, "found"])
                # save as csv file
                f_w.writerow(p95_list)
                # or save as txt file
                logging.error("p95_list,{}".format(p95_list))

            else:
                p95_list.extend([reward, i, "failed"])
                f_w.writerow(p95_list)
                logging.error("p95_list,{}".format(p95_list))

        stop_the_current_colocation()

        best_reward_id = np.argmax(reward_arms)
        best_config = chose_arm_storage[best_reward_id - 1]
        best_reward = reward_arms[best_reward_id]

        print(f"best config {best_config}, best reward {best_reward}")
        print(f"last config {core_list},{llc_config},{mb_config}, last reward {reward}")

        print(f'Mean reward of LinUCB with alpha = {alpha} is: ', np.mean(reward_arms))


def onlineEvaluate(mab, reward, reward_arms, chosen_arms, cumulative_reward, context, another_context, G, sample_times):
    """
    :param mab:
    :param rewards: ipc/delay
    :param contexts: counter
    :return:
    """

    mab.update(chosen_arms[0], chosen_arms[1], chosen_arms[2], reward, context, another_context)

    core_action, llc_action, band_action = mab.play(context, another_context,chosen_arms[0], chosen_arms[1], chosen_arms[2], sample_times)

    reward_arms.append(reward)

    G += reward
    cumulative_reward.append(G)

    chosen_arms = [core_action, llc_action, band_action]

    return reward_arms, chosen_arms, cumulative_reward, G


if __name__ == "__main__":
    llc_arm_orders, mb_arm_orders = get_llc_bandwith_config()
    # In the real sysytem, we identify the coming colocation  and get the PID of each job.
    # In the simulation experiment, we list the coming colocations in order, like the following example.
    colocation_list = [['img-dnn', 'xapian', "masstree"]]
    # In the simulation experiment, we list the loads for the coming colocations in order, like the following example.
    load_list = [[3,4,2]]

    # The performance counters we selected as shown in the paper
    performamce_counters = we_choose()
    nof_counters = len(performamce_counters)



    # select one way to save results
    # txt
    logging.basicConfig(
        filename=f"ttt.txt",level=logging.ERROR)
    # csv
    f = open("ttt.csv", "w", newline="")
    f_w = csv.writer(f)

    train_success(nof_counters=nof_counters,colocation_list=colocation_list,load_list=load_list,alpha=0.01,rounds=30,context_flag=1,F=60)
