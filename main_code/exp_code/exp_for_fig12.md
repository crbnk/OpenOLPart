> The purpose of the experiment is as follows:

> Evaluate the performance of OLPart with different number of versions of bandits.

> Randomly generate a coloation. Run OLPart over
the colocation with different number of versions of bandits.


Vary the parameter _F_ from 30 to 120 in the line 179 in./main_code/vote_bandit.py in the function _train_success_

Then fix _F_ at 60, vary the number of versions of bandits from 1 to 7 by adding the number of _mab_ in the line 36¡¢37

Then, run the following command in the server:

```
python vote_bandit.py
```