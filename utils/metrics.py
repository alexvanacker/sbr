import numpy as np
import copy

def MAP(rel,n) : 
    """ return the map
    
    n is the map param
    rel is the ordered list of 1 and 0
    good ref would be https://github.com/benhamner/Metrics/blob/master/Python/ml_metrics/average_precision.py
    """
    if n < len(rel) : 
        rel = rel[:n]
    n = len(rel)
    tot = 0
    cnt = 0
    for i, val in enumerate(rel) : 
        if val == 1: 
            cnt = cnt + 1
            tot = tot + float(cnt) / (i+1)
    return tot/n

def RDCG(rel) : 
    """ returns random dcg 
    """
    p = len(rel)
    indexes = np.arange(1,len(rel)+1)
    mydic = {}
    for item in rel :
        if item in mydic :
            mydic[item] = mydic[item] + 1
        else :
            mydic[item] = 1
    mysum = 0
    for key, val in mydic.iteritems() : 
        mysum = mysum + float(val)/p*(pow(2,key)-1)*sum(1/np.log2(indexes+1))
    return mysum

def DCG(rel) :
    """ returns dcg
    suppose rel already sorted by the rank predicted
    """ 
    indexes = np.arange(1,len(rel)+1)
    return sum((pow(2,rel)-1)/np.log2(indexes+1))

def IDCG(rel) : 
    """ returns best DCG possible
    no constaint on rel
    """
    p = len(rel)
    mydic = {}
    for item in rel :
        if item in mydic :
            mydic[item] = mydic[item] + 1
        else :
            mydic[item] = 1
    mysum = 0
    first = 1
    last = 0
    for key in sorted(mydic)[::-1] : 
        last = last + mydic[key]
        indexes = np.arange(first,last + 1)
        mysum = mysum + (pow(2,key)-1)*sum(1/np.log2(indexes+1))
        first = first + mydic[key] 
    return mysum

def NDCG(rel) :
    """ returns NDCG. 
    suppose rel already sorted by the rank predicted
    """
    return DCG(rel)/IDCG(rel)

def compare_random_ndcg(value_range = 3, size = 10, nb_iter = 100000) :
    """ 
    experimental proof of random ndcg value
    """
    myrel = np.random.randint(value_range,size=size)
    tot = 0
    mylist = []
    for i in range(nb_iter) : 
        rel = copy.copy(myrel)
        np.random.shuffle(rel) 
        tot  = tot + DCG(rel)
        mylist.append(tot/(i+1))
    tot = tot / nb_iter
    return (tot, RDCG(myrel))
    










