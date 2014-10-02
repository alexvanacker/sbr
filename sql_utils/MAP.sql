/*

MAP calculation in sql :
réf : https://www.kaggle.com/wiki/MeanAveragePrecision

- n main parameter
- has bought = 1 if user bought the product else 0
- row number = predicted rank. No ties. 

- demo of random is easy, just consider all permutation and everything got same chance to be at any place => bouyah 

*/


SELECT AVG(MAP_n) as MAP_n
	, AVG(MAP_n_random) as MAP_n_random
FROM (
    SELECT memberid
        , sum((row_number <= m and row_number <= n)::int * hasbought/row_number)/ LEAST(max(m),n) as MAP_n
        , sum((row_number <= m and row_number <= n)::int * /row_number)/ count(*) as MAP_n_random
    FROM (
    	SELECT memberid 
    		, has_bought
    		, row_number
    		, sum(hasbought) as m 
    		-- , count(*) as nb_tot
    	FROM MYTABLE ) s1
    GROUP BY memberid ) s2
; 