/*

MAP calculation in sql :
réf : https://www.kaggle.com/wiki/MeanAveragePrecision

- n main parameter of map
- has bought = 1 if user bought the product else 0
- row number = predicted rank. No ties. 

- close form of random seems to be hard to get contarry to ndcg. 

*/

SELECT AVG(MAP_n) as MAP_n
FROM (
    SELECT memberid
        , sum((row_number <= n)::int * hasbought * cumsum /row_number)/ LEAST(max(N),n) as MAP_n
    FROM (
    	SELECT memberid 
    		, has_bought -- 0 or 1 in what really happened
    		, row_number -- order of recommendations
            , sum(has_bought_sth) over(PARTITION by memberid order by row_number asc) as cumsum
    		, count(*) over (PARTITION BY memberid) as N -- nb of lines per user
    	FROM MYTABLE ) s1
    GROUP BY memberid ) s2
; 