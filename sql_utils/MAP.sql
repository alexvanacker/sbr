/*

MAP calculation in sql :
réf : https://www.kaggle.com/wiki/MeanAveragePrecision

- n main parameter
- has bought = 1 if user bought the product else 0
- row number = predicted rank. No ties. 

- comm : argh the pb is that I have 

*/


SELECT AVG(MAP_n) as MAP_n
FROM (
    SELECT memberid
        , sum((row_number <= m and row_number <= n)::int * hasbought/row_number)/ LEAST(m,n) as MAP_n
    FROM (
    	SELECT memberid 
    		, has_bought
    		, row_number
    		, sum(hasbought) as m 
    		, count(*) as nb_tot
    	FROM MYTABLE ) s1
    GROUP BY memberid ) s2
; 