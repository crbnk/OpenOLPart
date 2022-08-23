# OLPart: Online Learning based Resource Partitioning for Colocating Multiple Latency-Critical Jobs on Commodity Computers
OLPart is tested on a CentOS 7.8 Server with Linux 4.1.0 using Python3.7. Please install the following library depencies for running OLPart.


# The benchmark suites evaluated in Orchid

Tailbench: http://tailbench.csail.mit.edu

PARSEC 3.0: https://parsec.cs.princeton.edu/parsec3-doc.htm

# Run OLPart

## File Description
```
├─config: the config files and running commands for all evaluated jobs.
├─environment: some environment setting.
|   ├─env.sh: environment setting for running OLPart on the server at first time.
|   ├─rerun_docker.py: after each job has been instantiated in a separate container, 
|   |                   restart the server and use the code required for those jobs。
|   |─Dockerfile: the docker file to build containers.
|   |─correct_config.sh: the auxiliary file for Dockerfile.
├─main_code:
|  ├─get_max_load: get max load of LC job 
│    └─knee_all.py: the code for finding the QOS and max load of each LC job.      
|  ├─get_arm.py: generate resource configurations as arms.
|  ├─run_and_get_config.py : some tool functions.
|  ├─OLUCB.py: main algorithm of OLPart.
|  ├─vote_bandit.py : main file used to make online resource partitioning decisions.
```

## Run OLPart:
### Install Dependencies
```
pip3 install numpy   
sudo yum install intel-cmt-cat
sudo yum install msr-tools
sudo yum install docker
```
OLPart uses the Linux _perf_ to collect runtime status of each job for guiding the quick and smart exploration. 
Please ensure that Intel CAT, MBA, and taskset tools are supported and active in your system.
Click this link to confirm: https://github.com/intel/intel-cmt-cat.

### Instantiate jobs in the docker
Each job is instantiated in a separate container, we use _docker_ to create containers.
Please run _Dockerfile_ to create the containers. 
>The open-loop load generators for LC jobs are provided by Tailbench itself. All the load generators use exponential inter-arrival time
distributions to simulate a Poisson process, where requests are sent continuously and independently at a constant
average rate.

Then we record all evaluated jobs' docker ppid (as shown as _APP_DOCKER_PPID_ in file _run_and_get_config.py_ ).

```
docker top [container id]
```

Then we add config files to each evaluated job, the config files and running commands are in the directory _config_. 
Please copy the _sh_ and _py_ files to corrspond job's container.

Noted that we should set up the mapping address between the host and each docker to get latency information as the function  
_get_LC_app_latency_and_judge_ in file _run_and_get_config.py_.

docker run -t -d --name=[Name] -v [the address in host directory]:[the address in docker] [IMAGE], like:

```
docker run -t -d --name=img-dnn -v /home/crb/bandit_clite/share_data:/tmp/share bandit_last:v1
```

### Run
If you are running OLPart on the server for the first time, please run:
```
run ./env.sh
```
Then run the main file:
```
python vote_bandit.py
```
The functionality of the Class and Function involved in all Python files is shown in the comments in the codes.
