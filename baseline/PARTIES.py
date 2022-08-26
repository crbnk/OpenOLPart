# coding: utf-8
# Author: crb
# Date: 2021/8/31 17:00
import csv
import datetime
import logging
import random
import sys
import os
import time

import numpy as np
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from clite.clite import run_lc_benchmark,run_bg_benchmark,get_LC_app_latency_and_judge
from bandit.run_and_getconfig_qos import refer_core,gen_init_config,read_IPS_directlty,APP_docker_ppid
from bandit.get_arm_qos import arm_cor_numapp, get_llc_bandwith_config
import subprocess
TASKSET       = "sudo taskset -acp "
COS_CAT_SET1  = "sudo pqos -e \"llc:%s=%s\""
COS_CAT_SET2  = "sudo pqos -a \"llc:%s=%s\""
COS_MBG_SET1  = "sudo pqos -e \"mba:%s=%s\""
COS_MBG_SET2  = "sudo pqos -a \"core:%s=%s\""
COS_RESET     = "sudo pqos -R"


APP_QOSES = {
    'masstree': 100,  # 250.0 ,
    'xapian': 20,  # 200.0 ,
    'img-dnn': 50,  # 100.0 ,
    'sphinx': 1500,  # 2000.0,
    'moses': 500,  # 1000.0,
    'specjbb': 1,  # 10.0

}

def get_be_ipc(LC_APPS,BG_APPS,app_cores):
    APPS=LC_APPS+BG_APPS
    total_command = []
    insn_tmp = []

    for j in range(len(BG_APPS)):
        if BG_APPS[j] == 'canneal' or BG_APPS[j] == 'streamcluster':
            target = f"/tmp/parsec-3.0/pkgs/kernels/{BG_APPS[j]}/"
        else:
            target = f"/tmp/parsec-3.0/pkgs/apps/{BG_APPS[j]}/"

        cmd_run = "sudo ps aux | grep {}".format(target)
        out = os.popen(cmd_run).read()
        if len(out.splitlines()) < 2:
            print("====================rerun")
            run_bg_benchmark(BG_APPS, app_cores[j + len(LC_APPS)])
        insn_tmp.append(f"insn per cycle_{str(BG_APPS[j])}")
        re = subprocess.call(f'sudo taskset -apc {app_cores[j+ len(LC_APPS)]} {APP_docker_ppid[BG_APPS[j]]} > /dev/null', shell=True)

        perf_command = f"sudo perf stat -e {event} -C {app_cores[j + len(LC_APPS)]} sleep 0.5"
        total_command.append(perf_command)

    r = subprocess.run("&".join(total_command), shell=True, check=True,
               capture_output=True)
    r_ = str(r.stderr.decode())
    rs = r_.split('\n')
    label = dict.fromkeys(insn_tmp, 0)
    for index, line in enumerate(rs):
        rr = line.split(' ')
        rr = [i for i in rr if i != ""]
        if len(rr) < 2 or "elapsed" in rr:
            continue
        if "Performance" in line:
            cpu = line[39:-2]
            for i in range(len(BG_APPS)):
                if app_cores[i + len(LC_APPS)] == cpu:
                    label[f"insn per cycle_{APPS[i + len(LC_APPS)]}"] = float(rs[index + 3][55:59])
                    break
            continue

    now_ipc = list(label.values())
    for i in range(len(BG_APPS)):
        core = int(app_cores[len(LC_APPS) + i][-1]) - int(app_cores[len(LC_APPS) + i][0]) + 1
        now_ipc[i] *= core

    reward = sum(now_ipc)
    return reward

def main(LC_APPS,BE_APPS,lOAD_LIST):
    NUM_APPS = len(LC_APPS) + len(BE_APPS)
    APPS= BE_APPS+LC_APPS

    core_list,llc_config,mb_config,_ = gen_init_config(APPS,llc_arm_orders,alg="fair")
    time.sleep(1)
    run_bg_benchmark(BE_APPS, core_list[len(LC_APPS):])

    gen_init_resource_state(core_list,llc_config,mb_config)

    run_lc_benchmark(LC_APPS, lOAD_LIST, core_list)
    slacks = np.zeros(NUM_APPS)
    T = 0
    resource_wheel = 0
    logging.error("colocation,load_list, {} {}".format(APPS, lOAD_LIST))
    real_latency, flag = check_qos(LC_APPS)

    if flag == 0:
        print("Find solution")

        if BE_APPS != []:
            reward =get_be_ipc(LC_APPS,BE_APPS,core_list)
        else:
            reward = get_LC_app_latency_and_judge(LC_APPS)

        real_latency.extend([reward, T])
        logging.error("p95_list,{},".format(real_latency))
        return
    else:
        for i in range(len(LC_APPS)):
            slacks[i] = (APP_QOSES[LC_APPS[i]] - real_latency[i]) / APP_QOSES[LC_APPS[i]]

    pre_lantency = real_latency

    while True:
        # L: app_with_largest_slack  S: app_with_smallest_slack
        L = np.argmax(slacks)
        S = np.argmin(slacks)
        if slacks[S] < 0.05:
            app_cores = upsize(resource_wheel,L,S,LC_APPS,BE_APPS,lOAD_LIST)

            real_latency, flag = check_qos(LC_APPS)
            if flag == 0:
                if BE_APPS != []:
                    reward = get_be_ipc(LC_APPS,BE_APPS,app_cores)
                else:
                    reward = get_LC_app_latency_and_judge(LC_APPS)
                print("Find solution")

                real_latency.extend([reward, T])
                logging.error("p95_list,{},".format(real_latency))
                break
            else:
                for i in range(len(LC_APPS)):
                    slacks[i] = (APP_QOSES[LC_APPS[i]] - real_latency[i]) / APP_QOSES[LC_APPS[i]]

                if real_latency[S] > pre_lantency[S]:
                    # up flag
                    state_matrix[S][resource_wheel][1] = 1
                # change adjusted resource
                resource_wheel += 1
                if resource_wheel == 3:
                    resource_wheel = 0

                if BE_APPS != []:
                    reward = get_be_ipc(LC_APPS,BE_APPS,app_cores)
                else:
                    reward = get_LC_app_latency_and_judge(LC_APPS)
                real_latency.append(reward)
                logging.error("p95_list,{},".format(real_latency))
                pre_lantency = real_latency

        else:
            if slacks[L] > 0.2:
                app_cores = downsize(resource_wheel,L,S,LC_APPS,BE_APPS,lOAD_LIST)
                real_latency, flag = check_qos(LC_APPS)
                if flag == 0:
                    if BE_APPS != []:
                        reward = get_be_ipc(LC_APPS,BE_APPS,app_cores)
                    else:
                        reward = get_LC_app_latency_and_judge(LC_APPS)
                    print("Find solution")
                    real_latency.extend([reward, T])
                    logging.error("p95_list,{},".format(real_latency))
                    break
                else:
                    for i in range(len(LC_APPS)):
                        slacks[i] = (APP_QOSES[LC_APPS[i]] - real_latency[i]) / APP_QOSES[LC_APPS[i]]

                    if slacks[L] < 0.05:
                        # revert back
                        state_matrix[L][resource_wheel][0] += 1
                        state_matrix[S][resource_wheel][0] -= 1
                        # down flag
                        state_matrix[L][resource_wheel][1] = -1
                    # change adjusted resource
                    resource_wheel += 1
                    if resource_wheel == 3:
                        resource_wheel = 0
                    if BE_APPS != []:
                        reward = get_be_ipc(LC_APPS,BE_APPS,app_cores)
                    else:
                        reward = get_LC_app_latency_and_judge(LC_APPS)
                    real_latency.extend([reward, T])
                    logging.error("p95_list,{},".format(real_latency))
                    pre_lantency = real_latency



        T += 1
        if T > 60:
            print("Failed")
            logging.error("Failed")
            break



def check_qos(LC_APPS):
    real_latency = []
    flag = 0
    for i in range(len(LC_APPS)):
        p95 = get_LC_app_latency_and_judge(LC_APPS[i])
        real_latency.append(p95)
        if APP_QOSES[LC_APPS[i]] < p95:
            # met qos
            flag = 1

    return real_latency, flag


def take_action(be_id,L,S,chosen_app_id,chosen_resource_id,direction):
    def find_victim_app(be_id,L):
        if be_id != -1:
            return be_id
        else:
            # return app has max slack
            return L

    if direction == 1:
        V = find_victim_app(be_id,L)
        # move
        # can not higher than resources
        if state_matrix[chosen_app_id][chosen_resource_id][0] < resource_limit_dict[chosen_resource_id] and state_matrix[V][chosen_resource_id][0] != 1:
            state_matrix[chosen_app_id][chosen_resource_id][0] += 1
            state_matrix[V][chosen_resource_id][0] -= 1
            if state_matrix[chosen_app_id][chosen_resource_id][0] == state_matrix[V][chosen_resource_id][0]:
                state_matrix[V][chosen_resource_id][1] = 1
        else:
            state_matrix[chosen_app_id][chosen_resource_id][1] = -1
    else:
        V = S
        if state_matrix[chosen_app_id][chosen_resource_id][0] > 1:
            state_matrix[chosen_app_id][chosen_resource_id][0] -= 1
            state_matrix[V][chosen_resource_id][0] += 1
        else:
            state_matrix[chosen_app_id][chosen_resource_id][1] = 1






def gen_config(LC_APPS,BE_APPS):
    NUM_APPS = len(LC_APPS) + len(BE_APPS)
    app_cores, app_llcs, app_mbs = [], [], []
    for i in range(NUM_APPS):
        app_cores.append(int(state_matrix[i][0][0]))
        app_llcs.append(state_matrix[i][1][0])
        app_mbs.append(state_matrix[i][2][0])

    app_cores = refer_core(app_cores)

    for j in range(len(LC_APPS)):
        TASKSET + app_cores[j] + " " + APP_docker_ppid[LC_APPS[j]]
        COS_CAT_SET1 % (str(j + 1), app_llcs[j])
        COS_CAT_SET2 % (str(j + 1), app_cores[j])
        COS_MBG_SET1 % (str(j + 1), app_mbs[j])
        COS_MBG_SET2 % (str(j + 1), app_cores[j])

    time.sleep(2)
    return app_cores

def upsize(chosen_resource_id,L,S,LC_APPS,BE_APPS,lOAD_LIST):
    direction = state_matrix[S][chosen_resource_id][1]
    NUM_APPS = len(LC_APPS) + len(BE_APPS)

    if direction != 1:
        state_matrix[S][chosen_resource_id][1] = 1
    if BE_APPS != []:
        be_id = random.randint(len(LC_APPS), NUM_APPS-1)
    else:
        be_id = -1
    take_action(be_id,L,S,S,chosen_resource_id,direction)
    app_cores = gen_config(LC_APPS,BE_APPS)
    run_lc_benchmark(LC_APPS, lOAD_LIST, app_cores)
    # time.sleep(1)
    return app_cores



def downsize(chosen_resource_id,L,S,LC_APPS,BE_APPS,lOAD_LIST):
    direction = state_matrix[L][chosen_resource_id][1]
    NUM_APPS = len(LC_APPS) + len(BE_APPS)
    if direction != -1:
        state_matrix[L][chosen_resource_id][1] = -1
        if BE_APPS != []:
            be_id = random.randint(len(LC_APPS), NUM_APPS-1)
        else:
            be_id = -1
    take_action(be_id, L, S, L, chosen_resource_id, direction)
    app_cores = gen_config(LC_APPS,BE_APPS)
    run_lc_benchmark(LC_APPS, lOAD_LIST, app_cores)
    # time.sleep(1)
    return app_cores


def gen_init_resource_state(core_list,llc_config,mb_config):

    for i in range(len(mb_config)):

        state_matrix[i][0][0] = len(core_list[i].split(","))
        state_matrix[i][1][0] = llc_config[i][1] - llc_config[i][0]+1
        state_matrix[i][2][0] = mb_config[i]
    return state_matrix



if __name__ == "__main__":
    NUM_CORES = 9
    NUM_WAYS = 10
    NUM_BW = 10
    resource_limit_dict = {0:NUM_CORES,1:NUM_WAYS,2:NUM_BW}

    llc_arm_orders, mb_arm_orders = get_llc_bandwith_config()


    logging.basicConfig(
        filename=f"./parties_ttt.txt",
        level=logging.ERROR)


    colocation_list = ['img-dnn', 'xapian', "masstree"]

    for i in colocation_list:
        logging.error("colocation,load_list, {} {}".format(i,[4,4,4]))

        state_matrix = np.zeros((len(i), 3, 2))
        LC_APPS,BE_APPS=[],[]
        for j in i:
            if j in APP_QOSES.keys():
                LC_APPS.append(j)
            else:
                BE_APPS.append(j)
        LOAD_LIST=[4 for m in range(len(LC_APPS))]
        main(LC_APPS,BE_APPS,LOAD_LIST)