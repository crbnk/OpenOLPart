#!/usr/bin/python
import csv
import datetime
import logging
import os
import time
import shlex
import numpy as np
import random as rd
import subprocess as sp
from scipy import stats
from scipy.stats import norm
from scipy.optimize import minimize
import sklearn.gaussian_process as gp

# Number of LC apps available
TOT_LC_APPS = 5

# Number of BG apps available
TOT_BG_APPS = 6

# Number of QPS categories
N_QPS_CAT = 10

APP_NAMES = [
    'masstree',
    'xapian',
    'img-dnn',
    'sphinx',
    'moses',
    'specjbb'
]

APP_QOSES = {
    'masstree': 100,  # 250.0 ,
    'xapian': 20,  # 200.0 ,
    'img-dnn': 50,  # 100.0 ,
    'sphinx': 1500,  # 2000.0,
    'moses': 500,  # 1000.0,
    'specjbb': 1,  # 10.0

}
# QPS levels
APP_QPSES = {
    'masstree': list(range(50, 550, 50)),
    'xapian': list(range(80, 880, 80)),  # list(range(50, 550, 50))
    'img-dnn': list(range(140, 1540, 140)),  # list(range(50, 550, 50))
    'sphinx': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
    'moses': list(range(7, 77, 7)),  # list(range(10, 110, 10))
    'specjbb': list(range(300, 3300, 300))  # list(range(300, 3300, 300))
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

APP_docker_ppid = {
        'masstree' : "3135",
        'xapian'   : "3000",
        'img-dnn'  : "3248",
        'sphinx'   : "2881",
        'moses'    : "2604",
        'specjbb'  : "8900",
        'blackscholes' : "2476",
        'canneal'      : "2364",
        'fluidanimate' : "2211",
        'freqmine'     : "2056",
        'streamcluster': "1926",
        'swaptions'    : "1618"
      }
# Number of times acquisition function optimization is restarted
NUM_RESTARTS = 1

# Number of maximum iterations (max configurations sampled)
MAX_ITERS = 100


# Number of resources controlled
NUM_RESOURCES = 3

# Max values of each resources
NUM_CORES = 9
NUM_WAYS = 10
MEMORY_BW = 100

# Max units of (cores, LLC ways, memory bandwidth)
NUM_UNITS = [9, 10, 10]

# Configuration formats
CONFIGS_CORES = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
CONFIGS_CWAYS = ["0x1", "0x3", "0x7", "0xf", "0x1f", "0x3f", "0x7f", "0xff", "0x1ff", "0x3ff"]
CONFIGS_MEMBW = ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100"]



app_docker_dict = {
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

# Commands to set hardware allocations
TASKSET = "sudo taskset -acp "
COS_CAT_SET1 = "sudo pqos -e \"llc:%s=%s\""
COS_CAT_SET2 = "sudo pqos -a \"llc:%s=%s\""
COS_MBG_SET1 = "sudo pqos -e \"mba:%s=%s\""
COS_MBG_SET2 = "sudo pqos -a \"core:%s=%s\""
COS_RESET = "sudo pqos -R"

# Commands to get MSRs
WR_MSR_COMM = "wrmsr -a "
RD_MSR_COMM = "rdmsr -a -u "

# MSR register requirements
IA32_PERF_GBL_CTR = "0x38F"  # Need bits 34-32 to be 1
IA32_PERF_FX_CTRL = "0x38D"  # Need bits to be 0xFFF
MSR_PERF_FIX_CTR0 = "0x309"  # Counts INST_RETIRED.ANY

# Amount of time to sleep after each sample
SLEEP_TIME = 2

# Suppress application outputs
FNULL = open(os.devnull, 'w')

# Path to the base directory (if required)
BASE_DIR = "/path/to/base/directory/"

# All the LC apps being run
LC_APPS = ['masstree', 'img-dnn', 'xapian']

# All the BE jobs being runs
BE_APPS = ['streamcluster']


APPS = LC_APPS + BE_APPS

# QoSes of LC apps
APP_QOSES = [APP_QOSES[a] for a in LC_APPS]

# Number of apps currently running
NUM_LC_APPS = len(LC_APPS)

NUM_BE_APPS = len(BE_APPS)

NUM_APPS = NUM_LC_APPS + NUM_BE_APPS

# Total number of parameters
NUM_PARAMS = NUM_RESOURCES * (NUM_APPS - 1)

# Set expected value threshold for termination
EI_THRESHOLD = 0.01 ** NUM_APPS

# Global variable to hold baseline performances
BASE_PERFS = [0.0] * NUM_APPS

# Required global variables
BOUNDS = None

CONSTS = None

MODEL = None

OPTIMAL_PERF = None



def get_be_ipc(app_cores):
    total_command = []
    insn_tmp = []

    try:
        for j in range(len(BE_APPS)):
            if BE_APPS[j] == 'canneal' or BE_APPS[j] == 'streamcluster':
                target = f"/tmp/parsec-3.0/pkgs/kernels/{BE_APPS[j]}/"
            else:
                target = f"/tmp/parsec-3.0/pkgs/apps/{BE_APPS[j]}/"

            cmd_run = "sudo ps aux | grep {}".format(target)
            out = os.popen(cmd_run).read()
            if len(out.splitlines()) < 2:
                print("====================rerun")
                run_be_benchmark(BE_APPS, app_cores[j + len(LC_APPS)])

            re = sp.call(f'sudo taskset -apc {app_cores[j+ len(LC_APPS)]} {APP_docker_ppid[BE_APPS[j]]} > /dev/null', shell=True)
            insn_tmp.append(f"insn per cycle_{str(BE_APPS[j])}")
            perf_command = f"sudo perf stat -e {performamce_counters} -C {app_cores[j + len(LC_APPS)]} sleep 0.5"
            total_command.append(perf_command)

            r = sp.run("&".join(total_command), shell=True, check=True,
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
                    for i in range(len(BE_APPS)):
                        if app_cores[i + len(LC_APPS)] == cpu:
                            label[f"insn per cycle_{APPS[i + len(LC_APPS)]}"] = float(rs[index + 3][55:59])
                            break
                        continue


        sdd = [0.0] * NUM_BE_APPS
        now_ipc = list(label.values())
        for i in range(len(BE_APPS)):
            print(app_cores)
            core = int(app_cores[len(LC_APPS) + i][-1]) - int(app_cores[len(LC_APPS) + i][0]) + 1
            now_ipc[i] *= core
            sdd[i] = min(1.0, now_ipc[i] / BASE_PERFS[i + NUM_LC_APPS])

        reward = sum(now_ipc)
    except:
        reward=0
        sdd = [0.0] * NUM_BE_APPS
        for i in range(len(BE_APPS)):
            sdd[i] = min(1.0, 0 / BASE_PERFS[i + NUM_LC_APPS])

    return reward,sdd

def run_lc_benchmark(lc_list, load_list, core_list):
    total_command = []
    for i in range(len(lc_list)):
        qps = APP_QPSES[lc_list[i]][load_list[i]]
        cores = int(core_list[i][-1]) - int(core_list[i][0]) + 1
        command = f"docker exec {app_docker_dict[lc_list[i]]} taskset -c {core_list[i]} python /tmp/tailbench-v0.9/{lc_list[i]}/testtt.py {qps} {cores} &"
        total_command.append(command)

    sp.call(" ".join(total_command), shell=True, stdout=open(os.devnull, 'w'))


def run_be_benchmark(bg_list, core_list):
    total_command = []
    for i in range(len(bg_list)):
        cores = int(core_list[-len(bg_list) + i][-1]) - int(core_list[-len(bg_list) + i][0]) + 1
        command = f"docker exec {app_docker_dict[bg_list[i]]} taskset -c {core_list[i]} python /tmp/parsec-3.0/./run_crb.py {bg_list[i]} {cores} &"
        total_command.append(command)

    sp.call(" ".join(total_command), shell=True, stdout=open(os.devnull, 'w'))
    # warm up
    time.sleep(2)


def get_LC_app_latency_and_judge(lc_app_name):
    def get_lat(dir):
        with open(dir, "r") as f:
            ff = f.readlines()
            print(ff[0])
            assert "latency" in ff[0], "Lat file read failed!"
            a = ff[0].split("|")[0]
            lat = a[24:-3]
            return float(lat)

    dir = f'/home/crb/bandit_clite/share_data/{lc_app_name}.txt'
    while True:
        if os.path.exists(dir):
            if os.path.getsize(dir) != 0:
                # print("#####################################################",os.path.getsize(dir))
                # time.sleep(1)
                p95 = get_lat(dir)
                logging.error("{} {}".format(lc_app_name, p95))
                break

    sp.call(f"sudo rm /home/crb/bandit_clite/share_data/{lc_app_name}.txt", shell=True)
    return p95


def gen_bounds_and_constraints():
    global BOUNDS, CONSTS

    # Generate the bounds and constraints required for the optimizer
    BOUNDS = np.array([[[1, NUM_UNITS[r] - (NUM_APPS - 1)] for a in range(NUM_APPS - 1)] \
                       for r in range(NUM_RESOURCES)]).reshape(NUM_PARAMS, 2).tolist()

    CONSTS = []
    for r in range(NUM_RESOURCES):
        CONSTS.append(
            {'type': 'eq', 'fun': lambda x: sum(x[r * (NUM_APPS - 1):(r + 1) * (NUM_APPS - 1)]) - (NUM_APPS - 1)})
        CONSTS.append(
            {'type': 'eq', 'fun': lambda x: -sum(x[r * (NUM_APPS - 1):(r + 1) * (NUM_APPS - 1)]) + (NUM_UNITS[r] - 1)})


def gen_initial_configs():
    # Generate the maximum allocation configurations for all applications
    configs = [[1] * NUM_PARAMS for j in range(NUM_APPS)]

    for j in range(NUM_APPS - 1):
        for r in range(NUM_RESOURCES):
            configs[j][j + ((NUM_APPS - 1) * r)] = NUM_UNITS[r] - (NUM_APPS - 1)

    # Generate the equal partition configuration
    equal_partition = []
    for r in range(NUM_RESOURCES):
        for j in range(NUM_APPS - 1):
            equal_partition.append(int(NUM_UNITS[r] / NUM_APPS))
    configs.append(equal_partition)

    return configs


def get_baseline_perfs(configs):
    global BASE_PERFS

    for i in range(NUM_APPS):
        p = configs[i]

        # Core allocations of each job
        app_cores = [""] * NUM_APPS
        s = 0
        for j in range(NUM_APPS - 1):
            app_cores[j] = ",".join(
                [str(c) for c in list(range(s, s + p[j]))])
            s += p[j]
        app_cores[NUM_APPS - 1] = ",".join(
            [str(c) for c in list(range(s, NUM_UNITS[0]))])

        # L3 cache ways allocation of each job
        app_cways = [""] * NUM_APPS
        s = 0
        for j in range(NUM_APPS - 1):
            app_cways[j] = str(hex(
                int("".join([str(1) for w in list(range(p[j + NUM_APPS - 1]))] + [str(0) for w in list(range(s))]), 2)))

            s += p[j + NUM_APPS - 1]
        app_cways[NUM_APPS - 1] = str(
            hex(int("".join([str(1) for w in list(range(NUM_UNITS[1] - s))] + [str(0) for w in list(range(s))]), 2)))

        # Memory bandwidth allocation of each job
        app_membw = [""] * NUM_APPS
        s = 0
        for j in range(NUM_APPS - 1):
            app_membw[j] = str(p[j + 2 * (NUM_APPS - 1)] * 10)
            s += p[j + 2 * (NUM_APPS - 1)] * 10
        app_membw[NUM_APPS - 1] = str(NUM_UNITS[2] * 10 - s)

        run_lc_benchmark(LC_APPS, load_list, app_cores)

        # Set the allocations
        for j in range(NUM_APPS):
            TASKSET + app_cores[j] + " " + APP_docker_ppid[APPS[j]]
            COS_CAT_SET1 % (str(j + 1), app_cways[j])
            COS_CAT_SET2 % (str(j + 1), app_cores[j])
            COS_MBG_SET1 % (str(j + 1), app_membw[j])
            COS_MBG_SET2 % (str(j + 1), app_cores[j])

        if i >= NUM_LC_APPS:
            # Reset the IPS counters
            os.system("sudo " + WR_MSR_COMM + MSR_PERF_FIX_CTR0 + " 0x0")

        time.sleep(SLEEP_TIME)

        if i < NUM_LC_APPS:
            BASE_PERFS[i] = get_LC_app_latency_and_judge(LC_APPS[i])
        else:

            perf_command = f"sudo perf stat -e {performamce_counters} -C {app_cores[i]} sleep 0.5"

            r = sp.run(perf_command, shell=True, check=True,
                       capture_output=True)
            r_ = str(r.stderr.decode())
            rs = r_.split('\n')

            for index, line in enumerate(rs):
                rr = line.split(' ')
                rr = [ii for ii in rr if ii != ""]
                if len(rr) < 2 or "elapsed" in rr:
                    continue
                if "Performance" in line:
                    cpu = line[39:-2]
                    if app_cores[i] == cpu:
                        label = float(rs[index + 3][55:59])
                        break
                break


            core = int(app_cores[i][-1]) - int(app_cores[i][0]) + 1
            label *= core
            print(label)
            BASE_PERFS[i] = label

    return app_cores

def gen_random_config():
    # Generate a random configuration
    config = []
    for r in range(NUM_RESOURCES):
        total = 0
        remain_apps = NUM_APPS
        for j in range(NUM_APPS - 1):
            alloc = rd.randint(1, NUM_UNITS[r] - (total + remain_apps - 1))
            config.append(alloc)
            total += alloc
            remain_apps -= 1

    return config


def sample_perf(p):
    # Core allocations of each job
    app_cores = [""] * NUM_APPS
    s = 0
    for j in range(NUM_APPS - 1):
        app_cores[j] = ",".join(
            [str(c) for c in list(range(s, s + p[j]))])
        s += p[j]
    app_cores[NUM_APPS - 1] = ",".join(
        [str(c) for c in list(range(s, NUM_UNITS[0]))])

    # L3 cache ways allocation of each job
    app_cways = [""] * NUM_APPS
    s = 0
    for j in range(NUM_APPS - 1):
        app_cways[j] = str(
            hex(int("".join([str(1) for w in list(range(p[j + NUM_APPS - 1]))] + [str(0) for w in list(range(s))]), 2)))
        s += p[j + NUM_APPS - 1]
    app_cways[NUM_APPS - 1] = str(
        hex(int("".join([str(1) for w in list(range(NUM_UNITS[1] - s))] + [str(0) for w in list(range(s))]), 2)))

    # Memory bandwidth allocation of each job
    app_membw = [""] * NUM_APPS
    s = 0
    for j in range(NUM_APPS - 1):
        app_membw[j] = str(p[j + 2 * (NUM_APPS - 1)] * 10)
        s += p[j + 2 * (NUM_APPS - 1)] * 10
    app_membw[NUM_APPS - 1] = str(NUM_UNITS[2] * 10 - s)

    run_lc_benchmark(LC_APPS, load_list, app_cores)

    # Set the allocations
    for j in range(NUM_APPS):

        TASKSET + app_cores[j] + " " + APP_docker_ppid[APPS[j]]
        COS_CAT_SET1 % (str(j + 1), app_cways[j])
        COS_CAT_SET2 % (str(j + 1), app_cores[j])
        COS_MBG_SET1 % (str(j + 1), app_membw[j])
        COS_MBG_SET2 % (str(j + 1), app_cores[j])

    if NUM_BE_APPS != 0:
        # Reset the IPS counters
        os.system("sudo " + WR_MSR_COMM + MSR_PERF_FIX_CTR0 + " 0x0")

    # Wait for some cycles
    time.sleep(SLEEP_TIME)

    qv = [1.0] * NUM_LC_APPS
    sd = [1.0] * NUM_LC_APPS

    p95_list = []
    violate_flag = 0
    for j in range(NUM_LC_APPS):
        p95 = get_LC_app_latency_and_judge(LC_APPS[j])

        if p95 > APP_QOSES[j]:
            violate_flag = 1
            qv[j] = APP_QOSES[j] / p95
            sd[j] = BASE_PERFS[j] / p95
        p95_list.append(p95)

    if BE_APPS != []:
        reward,sdd = get_be_ipc(app_cores)


    if violate_flag == 0:
        print("==========================================find====================================================")
        print(reward)
        p95_list.append(reward)
        p95_list.append("Find_solution")
        logging.error("p95_list,{},".format(p95_list))
    else:
        p95_list.append(reward)
        p95_list.append("Failed")
        logging.error("p95_list,{},".format(p95_list))


    # Return the final objective function score if QoS not met
    if stats.mstats.gmean(qv) != 1.0:
        return qv, 0.5 * stats.mstats.gmean(qv)

    # Return the final objective function score if QoS met
    if NUM_BE_APPS == 0:
        return qv, 0.5 * (min(1.0, stats.mstats.gmean(sd)) + 1.0)

    # Return the final objective function score if BG jobs are present

    return qv, 0.5 * (min(1.0, stats.mstats.gmean(sdd)) + 1.0)


def expected_improvement(c, exp=0.01):
    # Calculate the expected improvement for a given configuration 'c'
    mu, sigma = MODEL.predict(np.array(c).reshape(-1, NUM_PARAMS), return_std=True)
    val = 0.0
    with np.errstate(divide='ignore'):
        Z = (mu - OPTIMAL_PERF - exp) / sigma
        val = (mu - OPTIMAL_PERF - exp) * norm.cdf(Z) + sigma * norm.pdf(Z)
        val[sigma == 0.0] = 0.0

    return -1 * val


def find_next_sample(x, q, y):
    # Generate the configuration which has the highest expected improvement potential
    max_config = None
    max_result = 1

    # Multiple restarts to find the global optimum of the acquisition function
    for n in range(NUM_RESTARTS):

        val = None

        # Perform dropout 1/4 of the times
        if rd.choice([True, True, True, False]):

            x0 = gen_random_config()

            val = minimize(fun=expected_improvement,
                           x0=x0,
                           bounds=BOUNDS,
                           constraints=CONSTS,
                           method='SLSQP')
        else:
            ind = rd.choice(list(range(len(y))))
            app = q[ind].index(max(q[ind]))

            if app == (NUM_APPS - 1):

                consts = []
                for r in range(NUM_RESOURCES):
                    units = sum(x[ind][r * (NUM_APPS - 1):(r + 1) * (NUM_APPS - 1)])
                    consts.append(
                        {'type': 'eq', 'fun': lambda x: sum(x[r * (NUM_APPS - 1):(r + 1) * (NUM_APPS - 1)]) - units})
                    consts.append(
                        {'type': 'eq', 'fun': lambda x: -sum(x[r * (NUM_APPS - 1):(r + 1) * (NUM_APPS - 1)]) + units})

                val = minimize(fun=expected_improvement,
                               x0=x[ind],
                               bounds=BOUNDS,
                               constraints=consts,
                               method='SLSQP')

            else:

                bounds = [[b[0], b[1]] for b in BOUNDS]

                for r in range(NUM_RESOURCES):
                    bounds[app + r * (NUM_APPS - 1)][0] = x[ind][app + r * (NUM_APPS - 1)]
                    bounds[app + r * (NUM_APPS - 1)][1] = x[ind][app + r * (NUM_APPS - 1)]

                val = minimize(fun=expected_improvement,
                               x0=x[ind],
                               bounds=bounds,
                               constraints=CONSTS,
                               method='SLSQP')

        if val.fun < max_result:
            max_config = val.x
            max_result = val.fun

    return -max_result, [int(c) for c in max_config]


def bayesian_optimization_engine(x0, alpha=1e-5):
    global MODEL, OPTIMAL_PERF

    x_list = []
    q_list = []
    y_list = []

    # Sample initial configurations
    for params in x0:
        x_list.append(params)
        q, y = sample_perf(params)
        q_list.append(q)
        y_list.append(y)

    xp = np.array(x_list)
    yp = np.array(y_list)

    # Create the Gaussian process model as the surrogate model
    kernel = gp.kernels.Matern(length_scale=1.0, nu=1.5)
    MODEL = gp.GaussianProcessRegressor(kernel=kernel, alpha=alpha, n_restarts_optimizer=1000, normalize_y=True)

    # Iterate for specified number of iterations as maximum
    for n in range(MAX_ITERS):

        # Update the surrogate model
        MODEL.fit(xp, yp)
        OPTIMAL_PERF = np.max(yp)

        # Find the next configuration to sample
        ei, next_sample = find_next_sample(x_list, q_list, y_list)

        # If the configuration is already sampled, carefully replace the sample
        mind = 0
        while next_sample in x_list:
            if mind == len(y_list):
                next_sample = gen_random_config()
                continue
            ind = sorted(enumerate(y_list), key=lambda x: x[1])[mind][0]
            if stats.mstats.gmean(q_list[ind]) == 1.0:
                mind += 1
                continue
            boxes = sum([q == 1.0 for q in q_list[ind]])
            if boxes == 0:
                mind += 1
                continue
            next_sample = [x for x in x_list[ind]]

            for r in range(NUM_RESOURCES):
                avail = NUM_UNITS[r]
                for a in range(NUM_LC_APPS - 1):
                    if q_list[ind][a] == 1.0:
                        flip = rd.choice([True, False])
                        if flip and next_sample[r * (NUM_LC_APPS - 1) + a] != 1.0:
                            next_sample[r * (NUM_LC_APPS - 1) + a] -= 1
                        avail -= next_sample[r * (NUM_LC_APPS - 1) + a]
                if q_list[ind][NUM_LC_APPS - 1] == 1.0:
                    flip = rd.choice([True, False])
                    unit = NUM_UNITS[r] - sum(next_sample[r * (NUM_LC_APPS - 1):(r + 1) * (NUM_LC_APPS - 1)])
                    if flip and unit != 1.0:
                        avail -= (unit - 1)
                    else:
                        avail -= unit
                cnf = [int(float(avail) / float(NUM_LC_APPS - boxes)) for b in range(NUM_LC_APPS - boxes)]
                cnf[-1] += avail - sum(cnf)
                i = 0
                for a in range(NUM_LC_APPS - 1):
                    if q_list[ind][a] != 1.0:
                        next_sample[r * (NUM_LC_APPS - 1) + a] = cnf[i]
                        i += 1
            mind += 1

        # Sample the new configuration
        x_list.append(next_sample)
        q, y = sample_perf(next_sample)
        q_list.append(q)
        y_list.append(y)

        xp = np.array(x_list)
        yp = np.array(y_list)

        # Terminate if the termination requirements are met
        if len(x_list)>30 :
            break
        # if ei < EI_THRESHOLD or np.max(yp) >= 0.99:
        #     break


    return n + 1, np.max(yp)


def c_lite():
    # Generate the bounds and constraints required for optimization
    gen_bounds_and_constraints()

    # Generate the initial set of configurations
    init_configs = gen_initial_configs()

    # Get the baseline performances with maximum allocations for each application
    app_cores = get_baseline_perfs(init_configs)
    run_be_benchmark(BE_APPS, app_cores[len(LC_APPS):])

    # Perform Bayesian optimization
    num_iters, obj_value = bayesian_optimization_engine(x0=init_configs)

    return num_iters, obj_value


def main():
    # Switch on the performance counters
    os.system("sudo " + WR_MSR_COMM + IA32_PERF_GBL_CTR + " 0x70000000F")
    os.system("sudo " + WR_MSR_COMM + IA32_PERF_FX_CTRL + " 0xFFF")

    # Print the header
    st = ''
    for a in range(NUM_APPS):
        st += 'App' + str(a) + ','
    st += 'ObjectiveValue' + ','
    st += '#Iterations'

    print(st)

    # Execute C-LITE
    num_iters, obj_value = c_lite()

    # Print the final results
    st = ''
    for a in LC_APPS:
        st += a + ','
    for a in BE_APPS:
        st += a + ','
    st += '%.2f' % obj_value + ','
    st += '%.2f' % num_iters

    print(st)


if __name__ == '__main__':
    performamce_counters = we_choose()
    logging.basicConfig(
        filename=f"./clite_ttt.txt",
        level=logging.ERROR)
    load_list = [4 for m in range(len(LC_APPS))]
    main()




