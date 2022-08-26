> The purpose of the experiment is as follows:

>Evaluate OLPart for more colocations to confirm that 
the advantage of OLPart is consistent for various colocations.

> Randomly generate 11 different colocations and
run the approaches for each colocation.


replace the commands in the line 158 and 160 in./main_code/vote_bandit.py with following codes
~~~
import random
colocation_list = [['moses', 'masstree', 'img-dnn', 'blackscholes'],
                     ['moses', 'sphinx', 'img-dnn', 'canneal'],
                     ['masstree', 'specjbb', 'img-dnn', 'canneal'],
                     ['img-dnn'', 'xapian', 'moses', 'fluidanimate'],
                     ['moses', 'sphinx', 'masstree', 'freqmine'],
                     ['moses', 'img-dnn', 'xapian', 'streamcluster'],
                     ['moses', 'specjbb', 'masstree', 'swaptions'],
                     ['img-dnn', 'xapian', 'moses', 'fluidanimate'],
                     ['moses', img-dnn', 'sphinx', 'swaptions'],
                     ['img-dnn', 'xapian', 'moses', 'streamcluster'],
                     ['img-dnn', 'xapian', 'masstree', 'blackscholes']]

load_list = []

for ii in range(len(colocation_list)):
    i = random.randint(4,9)
    j = random.randint(4,9)
    m = random.randint(4,9)
    load_list.append([i,j,m])

~~~

Then, run the following command in the server:

```
python vote_bandit.py
```