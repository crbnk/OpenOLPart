> The purpose of the experiment is as follows:

> Run a random colocation of three LC jobs and one BE job at different load settings to confirm that OLPart can significantly improve the
throughput of BE jobs.

> Run the colocation (xapian, img-dnn and moses,blackscholes) at different load settings,
and record the throughput of the BE job achieved by each approach over different load.

replace the commands in the line 161 and 163 in./main_code/vote_bandit.py with following codes
~~~
colocation_list = [['img-dnn', 'xapian', 'moses', 'blackscholes']]*1000
load_list = []

for i in range(9,-1,-1):
    for j in range(9,-1,-1):
        for m in range(9,-1,-1):
            load_list.append([i,j,m])

~~~

Then, run the following command in the server:

```
python vote_bandit.py
```