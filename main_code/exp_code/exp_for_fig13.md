> The purpose of the experiment is as follows:

> Evaluate the robustness of OLPart to dynamic load pressures.

>  Run a random colocation of 3 LC jobs and one BE job. Change the load of one of the LC jobs, while keep the
load of other jobs


replace the commands in the line 158 and 160 in./main_code/vote_bandit.py with following codes
```
LOAD_LIST = [[2, 1, 1, 0], [2, 1, 1, 0], [2, 1, 5, 0], [2, 1, 5, 0], [2, 1, 8, 0], [2, 1, 8, 0], [2, 1, 5, 0], [2, 1, 5, 0],
 [2, 1, 3, 0], [2, 1, 3, 0], [2, 1, 1, 0], [2, 1, 1, 0], [2, 1, 4, 0], [2, 1, 4, 0], [2, 1, 5, 0], [2, 1, 5, 0],
 [2, 1, 6, 0], [2, 1, 6, 0], [2, 1, 7, 0], [2, 1, 7, 0], [2, 1, 8, 0], [2, 1, 8, 0]]
 
colocation_list = [['img-dnn', "masstree", 'moses', 'fluidanimate']] * len(LOAD_LIST)
```
Then, run the following command in the server:

```
python vote_bandit.py
```