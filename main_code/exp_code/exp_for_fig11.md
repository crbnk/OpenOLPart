> The purpose of the experiment is as follows:

> Run colocations to compare the performance of OLPart
with/without contextual feature for confirming that the context
is helpful.

> Randomly generate a colocation, and run OLPart
on the colocation with and without context respectively. Run
each baseline approach for the colocation.


replace the commands in the line 161 and 163 in./main_code/vote_bandit.py.

```
colocation_list = [['img-dnn', 'xapian', 'moses', 'blackscholes']]*10

load_list = []

for i in range(0,10):
    load_list.append([i,i,i])

```

set the parameter _context_flag=0_ in the line 179 in./main_code/vote_bandit.py in the function _train_success_

Then, run the following command in the server:

```
python vote_bandit.py
```