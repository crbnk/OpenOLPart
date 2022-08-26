> The purpose of the experiment is as follows:

> Run the colocation which only contains LC jobs (img-dnn, xapian, moses) at 
different load to evaluate that OLPart can colocate LC jobs at much higher loads.

> Fix the load of img-dnn and xapian at some loads, and gradually increase
the load pressure of 'moses' find the highest tolerable load
for guaranteeing the QoS for all the three jobs.

> So we set up the experiment from high load pressure to low pressure, and the first load list 
that gives a positive reward is the maximum beared load list for LC jobs by the method.

replace the commands in the line 161 and 163 in./main_code/vote_bandit.py with following codes
~~~
colocation_list = [['img-dnn', 'xapian', 'moses']]*1000
load_list = []

for i in range(9,-1,-1):
    for j in range(9,-1,-1):
        for m in range(9,-1,-1):
            load_list.append([i,j,m])

~~~

To get a quick result, add the following code in the line 117 in ./main_code/vote_bandit.py 
in the condition (_if reward > 0_) 
~~~
break
~~~

Then, run the following command in the server:

```
python vote_bandit.py
```