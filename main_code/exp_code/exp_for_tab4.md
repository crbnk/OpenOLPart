> The purpose of the experiment is as follows:

> Run two colocations
consecutively under three different scenarios.

> Generate three pairs of colocations, with dfferent
numbers of jobs shared among the colocations in each pair. For
each pair of colocations, run OLPart over the two colocations
in the pair consecutively

replace the commands in the line 161 to 179 in ./main_code/vote_bandit.py as following:



```
# The performance counters we selected as shown in the paper
performamce_counters = we_choose()

# select one way to save results
# txt
logging.basicConfig(
    filename=f"ttt.txt",level=logging.ERROR)
# csv
f = open("ttt.csv", "w", newline="")
f_w = csv.writer(f)

colocation_list = [['specjbb', 'moses', 'sphinx','fluidanimate'],['img-dnn', 'xapian', 'masstree', 'blackscholes']]
load_list = [[5,6,5],[4,5,6]]
train_success(nof_counters=nof_counters,colocation_list=colocation_list,load_list=load_list,alpha=0.01,rounds=30,context_flag=1)


colocation_list = [['img-dnn', 'moses', 'sphinx','blackscholes'],['img-dnn', 'xapian', 'masstree','blackscholes']]
load_list = [[3,6,5],[4,8,6]]
train_success(nof_counters=nof_counters,colocation_list=colocation_list,load_list=load_list,alpha=0.01,rounds=30,context_flag=1)

colocation_list = [['img-dnn', 'xapian', 'masstree', 'blackscholes'], ['img-dnn', 'xapian', 'masstree', 'blackscholes']]
load_list = [[3,7,6],[7,8,4]]
train_success(nof_counters=nof_counters,colocation_list=colocation_list,load_list=load_list,alpha=0.01,rounds=30,context_flag=1

```

Then, run the following command in the server:

```
python vote_bandit.py
```