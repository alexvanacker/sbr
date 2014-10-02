/*

NDCG calculation in sql :
réf : http://www.kaggle.com/wiki/NormalizedDiscountedCumulativeGain

- rel is here in {0,1,2}
- ora is the optimal rank
- mra is the predicted rank

- generalization of formula are easy
- randomNDCG proof is simple : think permutation and realize that each line appears a constant nb of times at each position. 

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