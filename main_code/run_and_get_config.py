# coding: utf-8
# Author: crb
# Date: 2021/7/18 23:34
import datetime
import sys
import numpy as np
import time
from scipy import stats
import os
import subprocess

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

# Info:

LC_APP_NAMES = [
    'masstree',
    'xapian',
    'img-dnn',
    'sphinx',
    'moses',
    'specjbb'
]

# QoS requirements of LC apps (time in ms)
LC_APP_QOSES = {
    'masstree': 100,
    'xapian': 5,
    'img-dnn': 2,
    'sphinx': 1500,
    'moses': 500,
    'specjbb': 1
}
# Load
LC_APP_QPSES = {
    'masstree': list(range(30, 330, 30)),
    'xapian': list(range(600, 6000, 540)),
    'img-dnn': list(range(500, 4500, 400)),
    'sphinx': [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    'moses': list(range(50, 300, 25)),
    'specjbb': list(range(800, 8000, 720))
}

# BE apps
BCKGRND_APPS = [
    'blackscholes',
    'canneal',
    'fluidanimate',
    'freqmine',
    'streamcluster',
    'swaptions'
]
# Docker image id of each job
APP_DOCKER_DICT = {
    'masstree': "5069",
    'xapian': "3adb",
    'img-dnn': "306f",
    'sphinx': "f7eb",
    'moses': "ad58",
    'specjbb': "8900",
    'blackscholes': "881f",
    'canneal': "95d1",
    'fluidanimate': "b5ce",
    'freqmine': "cb3b",
    'streamcluster': "7bc0",
    'swaptions': "8b12"
}
# Docker ppid of each job
APP_DOCKER_PPID = {
    'masstree': "3135",
    'xapian': "3000",
    'img-dnn': "3248",
    'sphinx': "2881",
    'moses': "2604",
    'specjbb': "8900",
    'blackscholes': "2476",
    'canneal': "2364",
    'fluidanimate': "2211",
    'freqmine': "2056",
    'streamcluster': "1926",
    'swaptions': "1618"
}

# Get LC job's latency from LC job's output files
def get_LC_app_latency_and_judge(lc_app_name):
    def get_lat(dir):
        with open(dir, "r") as f:
            ff = f.readlines()
            assert "latency" in ff[0], "Lat file read failed!"
            a = ff[0].split("|")[0]
            lat = a[24:-3]
            return float(lat)

    tmp = []

    flag = 0
    for i in lc_app_name:
        # The address of your LC jobs' output file
        dir = lc_output_file
        while True:
            if os.path.exists(dir):
                if os.path.getsize(dir) != 0:
                    p95 = get_lat(dir)
                    tmp.append(p95)
                    break

        if p95 > LC_APP_QOSES[i]:
            flag = 1
    subprocess.call(f"sudo rm {lc_output_file}", shell=True)

    if flag == 1:
        return -1, tmp
    else:
        return 1, tmp

def get_now_ipc(lc_app, be_app, load_list,performance_counters):
    # Return contextual information and reward
    # Use perf command to get the values of selected counters
    run_lc_benchmark(lc_job,load_list, load_list[col_items])

    context_feature, counters_without_self, ipc = perf_app(lc_app,be_app,performance_counters)
    # Simple feature processing, normalized to [1,10]
    context_feature, counters_without_self = normalization(context_feature, counters_without_self)
    # Get the reward，if QoS are satisfied, the sum of IPCs of the BE jobs is returned; otherwise, -1 is returned
    reward, latency = get_LC_app_latency_and_judge(lc_app)
    if reward == 1:
        if be_app != []:
            reward = ipc

    return context_feature, counters_without_self, reward, latency


def l_r_convert_config(left, right):
    if type(left) != int:
        try:
            left = int(left)
        except:
            left = int(float(left.strip('\'& \"')))
    if type(right) != int:
        try:
            right = int(right)
        except:
            right = int(float(right.strip('\'& \"')))

    bin_string = []
    for m in range(1, 12):
        if left <= m <= right:
            bin_string.append(1)
        else:
            bin_string.append(0)
    sum1 = bin_string[0] * 2 + bin_string[1]
    sum2 = bin_string[2] * 8 + bin_string[3] * 4 + bin_string[4] * 2 + bin_string[5]
    sum3 = bin_string[6] * 8 + bin_string[7] * 4 + bin_string[8] * 2 + bin_string[9]
    ans = "0x" + str(sum1) + str(hex(sum2)[-1]) + str(hex(sum3)[-1])
    return ans


def refer_core(core_config):
    app_cores = [""] * len(core_config)
    endpoint_left = 0
    for i in range(len(core_config)):
        endpoint_right = endpoint_left + core_config[i] - 1
        app_cores[i] = ",".join([str(c) for c in list(range(endpoint_left, endpoint_right + 1))])
        endpoint_left = endpoint_right + 1
    # Num_of_cores: the CPU cores your server have
    assert endpoint_right <= num_of_cores, f"print {app_cores},give wrong cpu config"
    return app_cores


def gen_init_config(app_id, llc_arm_orders, alg="fair"):
    # Init resource config: equal allocation
    app_num = len(app_id)
    # Max units of (cores, LLC ways, memory bandwidth)
    nof_core = 9
    nof_llc = 10
    nof_mb = 10
    if alg == "fair":
        each_core_config = nof_core // app_num
        res_core_config = nof_core % app_num
        core_config = [each_core_config] * (app_num - 1)
        if res_core_config >= each_core_config:
            for i in range(res_core_config):
                core_config[i] += 1
            core_config.append(1)
        else:
            core_config.append(each_core_config + res_core_config)

        core_list = refer_core(core_config)

        arms = [i - 1 for i in core_config]
        core_arms = dict(zip(app_id, arms))

        endpoint_left = 1
        each_llc_config = nof_llc // app_num
        llc_config = []
        llc_arms = {}.fromkeys(app_id)

        for i in range(app_num):
            if i == app_num - 1:
                tmp_l = [endpoint_left, 10]
                llc_config.append(tmp_l)
                for j in range(len(llc_arm_orders)):
                    if llc_arm_orders[j] == tmp_l:
                        llc_arms[app_id[i]] = j
                break
            endpoint_right = endpoint_left + each_llc_config - 1
            tmp_l = [endpoint_left, endpoint_right]
            llc_config.append(tmp_l)
            for j in range(len(llc_arm_orders)):
                if llc_arm_orders[j] == tmp_l:
                    llc_arms[app_id[i]] = j
            endpoint_left = endpoint_right + 1

        each_mb_config = nof_mb // app_num
        res_mb_config = nof_mb % app_num
        mb_config = [each_mb_config] * (app_num - 1)

        if res_mb_config > each_mb_config:
            for i in range(res_mb_config):
                mb_config[i] += 1
            mb_config.append(1)
        else:
            mb_config.append(each_mb_config + res_mb_config)

        arms = [i - 1 for i in mb_config]
        mb_arms = dict(zip(app_id, arms))
        chosen_arms = [core_arms, llc_arms, mb_arms]

        for i in range(len(core_config)):
            subprocess.call(f'sudo taskset -apc {core_list[i]} {APP_DOCKER_PPID[app_id[i]]} > /dev/null',
                            shell=True)

            subprocess.run('sudo pqos -a "llc:{}={}"'.format(i, core_list[i]), shell=True, capture_output=True)
            subprocess.run('sudo pqos -e "llc:{}={}"'.format(i, l_r_convert_config(llc_config[i][0], llc_config[i][1])),
                           shell=True, capture_output=True)
            subprocess.run('sudo pqos -a "core:{}={}"'.format(i, core_list[i]), shell=True,
                           capture_output=True)
            subprocess.run('sudo pqos -e "mba:{}={}"'.format(i, int(float(mb_config[i])) * 10), shell=True,
                           capture_output=True)
        print("gen_init", core_list, llc_config, mb_config, chosen_arms)
        return core_list, llc_config, mb_config, chosen_arms


def gen_config(app_id, chosen_arms, llc_arm_orders, mb_arm_orders):
    core_arm, llc_arm, mb_arm = chosen_arms[0], chosen_arms[1], chosen_arms[2]
    core_config, llc_config, mb_config = [], [], []
    for key in core_arm.keys():
        llc_config.append(llc_arm_orders[llc_arm[key]])
        mb_config.append(mb_arm_orders[mb_arm[key]])
        core_config.append(core_arm[key])

    core_list = refer_core(core_config)

    for i in range(len(core_config)):
        subprocess.call(f'sudo taskset -apc {core_list[i]} {APP_DOCKER_PPID[app_id[i]]} > /dev/null', shell=True)
        subprocess.run('sudo pqos -a "llc:{}={}"'.format(i, core_list[i]), shell=True, capture_output=True)
        subprocess.run('sudo pqos -e "llc:{}={}"'.format(i, l_r_convert_config(llc_config[i][0], llc_config[i][1])),
                       shell=True, capture_output=True)
        subprocess.run('sudo pqos -a "core:{}={}"'.format(i, core_list[i]), shell=True,
                       capture_output=True)
        subprocess.run('sudo pqos -e "mba:{}={}"'.format(i, int(float(mb_config[i])) * 10), shell=True,
                       capture_output=True)
    return core_list, llc_config, mb_config


def run_be_benchmark(be_list,core_list):
    # Persistent running
    total_command = []

    for i in range(len(be_list)):
        cores=  int(core_list[-1]) - int(core_list[0]) + 1
        command = f"docker exec {app_docker_dict[be_list[i]]} taskset -c {core_list[i]} python /tmp/parsec-3.0/./run_parsec-3.0.py {bg_list[i]} {cores} &"
        total_command.append(command)
    subprocess.call(" ".join(total_command), shell=True, stdout= open(os.devnull, 'w'))
    # warm up
    time.sleep(2)


def run_lc_benchmark(lc_list, load_list,core_list):
    # inputs:['masstree','moses','img-dnn'],[1,2,5],["0-3","4-6","7-8"]
    # notes that: the values in load_list is between [0,9]
    total_command = []
    for i in range(len(lc_list)):
        print(i,lc_list[i],load_list[i])
        qps = LC_APP_QPSES[lc_list[i]][load_list[i]]
        cores = int(core_list[i][-1]) - int(core_list[i][0]) +1
        command = f"docker exec {app_docker_dict[lc_list[i]]} taskset -c {core_list[i]} python /tmp/tailbench-v0.9/{lc_list[i]}/run_tail.py {lc_list[i]}{qps} {cores} &"
        total_command.append(command)
    subprocess.call(" ".join(total_command), shell=True, stdout= open(os.devnull, 'w'))

def stop_the_current_colocation():
    subprocess.call("sudo kill -9 $(ps -ef|grep /tmp/tailbench.inputs/|grep -v grep|awk '{print $2}')",shell=True)
    #subprocess.call("sudo kill -9 $(ps -ef|grep /tmp/parsec-3.0/pkgs/|grep -v grep|awk '{print $2}')",shell=True)