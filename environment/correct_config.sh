#!/bin/bash

### 1. correct the file 'tailbench-v0.9/configs.sh'
mkdir /home/scratch_data
CONFIG_PATH=/home/tailbench-v0.9/configs.sh

DATA_ROOT=/home/tailbench.inputs
JDK_PATH=/usr/lib/jvm/java-8-openjdk-amd64
SCRATCH_DIR=/home/scratch_data

sed -i "s#/topleveldatadir#${DATA_ROOT}#g" ${CONFIG_PATH}
sed -i "s#/pathtojdk#${JDK_PATH}#g" ${CONFIG_PATH}
sed -i "s#/pathtoscratch#${SCRATCH_DIR}#g" ${CONFIG_PATH}

### 2. correct the file 'tailbench-v0.9/Makefile.config'
MAKEFILE_CONFIG_PATH=/home/tailbench-v0.9/Makefile.config

sed -i "s#/pathtojdk#${JDK_PATH}#g" ${MAKEFILE_CONFIG_PATH}

### 3. prepare 'harness'
cd /home/tailbench-v0.9/
./build.sh harness

### 4. prepare app 'silo'
SILO_MAKFILE_PATH=/home/tailbench-v0.9/silo/Makefile

sed -i '$!N;/\n.*Werror/!P;D' ${SILO_MAKFILE_PATH}
sed -i '/Werror/d' ${SILO_MAKFILE_PATH}

./build.sh silo

### 5. prepare app 'img-dnn'
./build.sh img-dnn

### 6. prepare app 'masstree'
ln -s /usr/lib/libtcmalloc_minimal.so.4 /usr/lib/libtcmalloc_minimal.so

./build.sh mastree

### 7. prepare app 'moses'
./build.sh moses

### 8. prepare app 'shore'
SHORE_RUN_PATH=/home/tailbench-v0.9/shore/run.sh

sed -i "s#/doesnotexist#/tmp#g" ${SHORE_RUN_PATH}

./build.sh shore

### 9. perpare app 'specjbb'
./build.sh specjbb

### 10. prepare app 'sphinx'
SPHINX_MAKFILE_PATH=/home/tailbench-v0.9/sphinx/Makefile

sed -i 's#`\$#` \$#g' /home/tailbench-v0.9/sphinx/Makefile

./build.sh sphinx

### 11. prepare app 'xapian'
./build.sh xapian
