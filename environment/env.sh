#!/bin/bash
# Close turbo boost
sudo modprobe msr
sudo rdmsr -a 0x1a0 -f 38:38
sudo wrmsr -a 0x1a0 0x4000850089
sudo rdmsr -a 0x1a0 -f 38:38
# Bind sysytem threads to a idle core for increasing the interferences like CPU core 9 in the example
sudo pqos -a "llc:9=9"
sudo pqos -e "llc:9=0x400"
sudo ps -To pid -A |grep -v PID >~/tmppid.txt
for pid_0 in `cat ~/tmppid.txt`
do
  sudo taskset -apc 9 $pid_0
done
