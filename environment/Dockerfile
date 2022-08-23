FROM ubuntu:16.04
MAINTAINER crb <chenrb@nbjl.nankai.edu.cn>

RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list

RUN apt clean

RUN apt update -y

RUN apt install -y uuid-dev libssl-dev libaio-dev google-perftools libboost-all-dev libboost-dev libboost-test-dev openjdk-8-jdk libjemalloc-dev libnuma-dev libpthread-stubs0-dev libxapian-dev libreadline-dev libdb5.3-dev libdb5.3++-dev libgtop2-dev libopencv-dev autoconf libncurses-dev ant libtool swig bison libbz2-dev git autoconf libgtop2-dev libreadline6 libreadline6-dev libncurses-dev libjemalloc-dev libdb++-dev libaio1 libssl-dev libcrypto++-dev python-dev swig python-numpy python-scipy

RUN wget http://tailbench.csail.mit.edu/tailbench-v0.9.tgz

RUN wget http://tailbench.csail.mit.edu/tailbench.inputs.tgz

WORKDIR /home

ADD tailbench* /home/
ADD correct_config.sh /home/

RUN chmod 777 /home/correct_config.sh
RUN /home/correct_config.sh
