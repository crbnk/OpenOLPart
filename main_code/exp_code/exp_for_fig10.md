> The purpose of the experiment is as follows:

> Run colocations with differnent sizes to evaluate the scalability of OLPart.

> Randomly generate 20 colocations for each size
ranging from 2-jobs to 6-jobs with random loads for LC jobs, and run all the approaches for
each colocation


replace the commands in the line 161 and 163 in./main_code/vote_bandit.py with new colocations and 
load list as described above.


Then, run the following command in the server:

```
python vote_bandit.py
```
