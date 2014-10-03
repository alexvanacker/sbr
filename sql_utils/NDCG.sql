/*

NDCG calculation in sql :
réf : http://www.kaggle.com/wiki/NormalizedDiscountedCumulativeGain

- rel is here in {0,1,2}
- ora is the optimal rank
- mra is the predicted rank

- generalization of formula are easy
- randomNDCG proof is simple : think permutation and realize that each line appears a constant nb of times at each position. 

-- case , rel in {0,1}
E(nDCG) = ((K/p)*sum(1/log2(i+1))) / IDCG
with K = sum(rel_i), p = length of list
IDCG = sum_i=1^K(1/log2(i+1))

-- case , rel in {0,1,2}
E(nDCG) = ((K1/p)*sum(1/log2(i+1))+(K2/p)*sum(3/log2(i+1))) / IDCG
K1 = nb rel = 1, k2 = nb rel = 2, p length of list
IDCG = sum_i=1^K2(3/log2(i+1)) + sum_i=K2+1^K2+k1(1/log2(i+1))

-- case rel in k (sorted list, asc) of size L, first index 1.
Lj is size of rel = kj
E(nDCG) = (sum_j((kj/p)*sum(2^kj -1 /log2(i+1)))) / IDCG
IDCG = sum_j(sum_i=1^K2(2^(k_(L-j))/log2(i+sum_(l<j)(kl)+1))) 

*/


SELECT AVG(DCG/IDCG) as NDCG
    , AVG(randomDCG/IDCG) as NDCG_random
FROM (
    SELECT memberid
        , sum((mra=1)::int * rel + (mra!=1)::int * (pow(2,rel)-1)/log(2,mra+1)) as DCG
        , sum((ora=1)::int * rel + (ora!=1)::int * (pow(2,rel)-1)/log(2,ora+1)) as IDCG
        , sum(has_bought_sth)/count(*) * sum(3 /log(2,ora+1)) + sum(nb_att)/count(*) *sum(1/log(2,ora+1)) as randomDCG
    FROM MYTABLE
    GROUP BY memberid ) s1
; 