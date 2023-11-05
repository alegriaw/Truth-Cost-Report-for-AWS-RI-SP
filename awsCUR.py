import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from awsAthena import run_query


        


def getLinkedAcct_SP_usage(table_name,database,s3_bucket,day_range,start_date,end_date,LinkedAccount_string):
    # query_sql = "select * from test_jayhuang_cur limit 2"
    # print(f"getLinkedAcct_SP_usage LinkedAccount_string: {LinkedAccount_string}")
    
    query_sql = ("""
        with sp_covered AS 
            (SELECT 
                date(line_item_usage_end_date) as bill_date,
                line_item_usage_account_id as LinkedAccount,
                product_servicecode,
                -- product_instance_type_family,
                -- product_location,
                SUM(pricing_public_on_demand_cost) AS spend_covered_by_sp
            FROM """+table_name+""" 
            WHERE line_item_line_item_type = 'SavingsPlanCoveredUsage'
                    AND product_servicecode = 'AmazonEC2'
                    AND line_item_usage_type LIKE '%Box%'
                    AND line_item_usage_type NOT LIKE '%Spot%'
                    AND line_item_usage_end_date >= (current_date - interval '"""+day_range+"""' day)
                    -- AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""')
            GROUP BY 1,2,3
            UNION ALL
            SELECT 
                date(line_item_usage_end_date)as bill_date,
                line_item_usage_account_id as LinkedAccount,
                product_servicecode,
                -- product_instance_type_family,
                -- product_location,
                SUM(pricing_public_on_demand_cost)
            FROM """+table_name+"""  
            WHERE line_item_line_item_type = 'SavingsPlanCoveredUsage'
                    AND product_servicecode = 'AmazonECS'
                    AND line_item_usage_type LIKE '%Fargate%'
                    AND line_item_usage_type NOT LIKE '%Spot%'
                    AND line_item_usage_end_date >= (current_date - interval '"""+day_range+"""' day)
                    -- AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""')
            GROUP BY 1,2,3
            UNION ALL
            SELECT 
                date(line_item_usage_end_date)as bill_date,
                line_item_usage_account_id as LinkedAccount,
                product_servicecode,
                -- product_instance_type_family,
                -- product_location,
                SUM(pricing_public_on_demand_cost)
            FROM """+table_name+"""  
            WHERE line_item_line_item_type = 'SavingsPlanCoveredUsage'
                    AND product_servicecode = 'AWSLambda'
                    AND line_item_usage_end_date >= (current_date - interval '"""+day_range+"""' day)
                    -- AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""')
            GROUP BY 1,2,3 )
            ,Total_cost AS 
            (SELECT 
                date(line_item_usage_end_date)as bill_date,
                line_item_usage_account_id as LinkedAccount,
                product_servicecode,
                -- product_instance_type_family,
                -- product_location,
                SUM(pricing_public_on_demand_cost) AS totalCost
            FROM """+table_name+"""  
            WHERE (line_item_line_item_type = 'SavingsPlanCoveredUsage'
                    OR line_item_line_item_type ='Usage')
                    AND product_servicecode = 'AmazonEC2'
                    AND line_item_usage_type NOT LIKE '%Spot%'
                    AND line_item_usage_type LIKE '%Box%'
                    AND line_item_usage_end_date >= (current_date - interval '"""+day_range+"""' day)
                    -- AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""')
            GROUP BY 1,2,3
            UNION ALL
            SELECT 
                date(line_item_usage_end_date)as bill_date,
                line_item_usage_account_id as LinkedAccount,
                product_servicecode,
                -- product_instance_type_family,
                -- product_location,
                SUM(pricing_public_on_demand_cost)
            FROM """+table_name+"""  
            WHERE (line_item_line_item_type = 'SavingsPlanCoveredUsage'
                    OR line_item_line_item_type ='Usage')
                    AND product_servicecode = 'AmazonECS'
                    AND line_item_usage_type NOT LIKE '%Spot%'
                    AND line_item_usage_type LIKE '%Fargate%'
                    AND line_item_usage_end_date >= (current_date - interval '"""+day_range+"""' day)
                    -- AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""')
            GROUP BY 1,2,3
            UNION ALL
            SELECT 
                date(line_item_usage_end_date)as bill_date,
                line_item_usage_account_id as LinkedAccount,
                product_servicecode,
                -- product_instance_type_family,
                -- product_location,
                SUM(pricing_public_on_demand_cost)
            FROM """+table_name+"""  
            WHERE (line_item_line_item_type = 'SavingsPlanCoveredUsage'
                    OR line_item_line_item_type ='Usage')
                    AND product_servicecode = 'AWSLambda'
                    AND line_item_usage_end_date >= (current_date - interval '"""+day_range+"""' day)
                    -- AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""')
                -- AND line_item_usage_account_id = '138046196805'
            GROUP BY 1,2,3 )
            
            , total_amt AS(
            SELECT   -- Total_cost.bill_date,
                    Total_cost.LinkedAccount AS LinkedAccount,
                    -- Total_cost.product_servicecode, 
                    -- total_cost.product_instance_type_family,
                    -- total_cost.product_location,
                    sum( IF(sp_covered.spend_covered_by_sp>=0,sp_covered.spend_covered_by_sp,0 ) ) AS totalSpend_SP_covered,
                    sum(totalCost - IF(sp_covered.spend_covered_by_sp>=0,sp_covered.spend_covered_by_sp,0 ) ) AS TotalOD_cost
                    -- sp_covered.spend_covered_by_sp/total_cost AS coverage
            FROM sp_covered full outer
            JOIN Total_cost
                ON  sp_covered.LinkedAccount = Total_cost.LinkedAccount
                    AND sp_covered.product_servicecode = Total_cost.product_servicecode
                    and sp_covered.bill_date =  Total_cost.bill_date
            
            group by 1 
            )
            
            select
                current_date as today,
                (current_date - interval '"""+day_range+"""' day) as pre_60days,
                LinkedAccount, 
                cast(totalSpend_SP_covered as int) as totalSpend_SP_covered ,
                cast(TotalOD_cost as int) as totalSpend_OD_covered,
                Cast((CASE WHEN totalSpend_SP_covered = 0 THEN 0 WHEN TotalOD_cost = 0 THEN 100.0 ELSE (totalSpend_SP_covered / (totalSpend_SP_covered + TotalOD_cost))*100 END) as int) "coverage (%)"
            from total_amt 
            -- where LinkedAccount in ('xx692520930' ,'xx3476550721')
            where LinkedAccount in """+LinkedAccount_string+""" 
            order by LinkedAccount asc

        """)

    # print(f"query_sql: {query_sql}")

    results = run_query(query_sql,database,s3_bucket)
    # print(results)
    # for result in results:
    #     print(result['identity_line_item_id'])
    # for result in results:
    #     if result["product"] not in ri_detail:
    #         ri_detail[result["product"]] = {}
        
    #     if result["account"] not in ri_detail[result["product"]]:
    #         ri_detail[result["product"]][result["account"]] = {}

    #     ri_detail[result["product"]][result["account"]]["sum_od_cost"] = result["sum_od_cost"]
    #     ri_detail[result["product"]][result["account"]]["sum_ri_cost"] = result["sum_ri_cost"]

    #     f.write(result["product"]+","+result["account"]+","+result["sum_od_cost"]+","+result["sum_ri_cost"]+"\n")

    # f.close()
    return results



def getLinkedAcct_RI_coverage(table_name,database,s3_bucket,day_range,service_name,start_date,end_date, LinkedAccount_string):
    # query_sql = "select * from test_jayhuang_cur limit 2"
    # print(f"getLinkedAcct_RI_coverage LinkedAccount_string: {LinkedAccount_string}")
    
    query_sql = ("""
        WITH 
        results AS ( 
        SELECT 
        date_format(line_item_usage_start_date, '%M %Y') billing_date 
        , date(line_item_usage_end_date) as billing_end_date 
        , product_region 
        , line_item_usage_account_id 
        , product_instance_type 
        , product_database_engine 
        , line_item_usage_type 
        , product_deployment_option 
        , sum(line_item_unblended_cost) on_demand_cost 
        , sum((CASE WHEN (line_item_line_item_description LIKE '%reserved instance applied%') THEN line_item_usage_amount ELSE 0 END)) reservation_covered_hours 
        , sum((CASE WHEN (line_item_line_item_description LIKE '%instance hour (or partial hour)%' OR line_item_line_item_description LIKE '%running%') THEN CAST(line_item_usage_amount AS double) ELSE 0 END)) on_demand_hours 
        FROM """+table_name+""" 
        WHERE line_item_product_code LIKE 
        '%"""+service_name+"""%'
        -- 'AmazonElastiCache' 
        -- '%RDS%' 
        AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""') 
        -- Linked account IDs
        -- AND line_item_usage_account_id in ('xx6692520930' ,'xx3476550721')
        AND line_item_usage_account_id in """+LinkedAccount_string+"""
        AND (line_item_line_item_description LIKE '%reserved instance applied%' OR line_item_line_item_description LIKE '%instance hour (or partial hour)%' OR line_item_line_item_description LIKE '%running%') 
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8 
        ) 
        ,results_b AS ( 
        SELECT 
        results.product_region, 
        results.line_item_usage_account_id , 
        sum(results.on_demand_hours) as on_demand_hours, 
        sum(results.reservation_covered_hours) as reservation_covered_hours, 
        sum(results.on_demand_cost) as on_demand_cost 
        FROM 
        results 
        group by 1,2 
        ) 
        -- final coverage rate count 
        SELECT 
        results_b.product_region, 
        results_b.line_item_usage_account_id as Linked_AccountID , 
        results_b.reservation_covered_hours, 
        results_b.on_demand_hours, 
        Cast((CASE WHEN results_b.reservation_covered_hours = 0 THEN 0 WHEN results_b.on_demand_hours = 0 THEN 100.0 ELSE (results_b.reservation_covered_hours / (results_b.reservation_covered_hours + results_b.on_demand_hours))*100 END) as int) "coverage (%)", 
        cast(results_b.on_demand_cost as int) as "on_demand_cost ($)" 
        FROM 
        results_b 
        ORDER BY 4 ASC

        """)

    # print(f"query_sql: {query_sql}")

    results = run_query(query_sql,database,s3_bucket)
    print(results)
    # for result in results:
    #     print(result['identity_line_item_id'])
    # for result in results:
    #     if result["product"] not in ri_detail:
    #         ri_detail[result["product"]] = {}
        
    #     if result["account"] not in ri_detail[result["product"]]:
    #         ri_detail[result["product"]][result["account"]] = {}

    #     ri_detail[result["product"]][result["account"]]["sum_od_cost"] = result["sum_od_cost"]
    #     ri_detail[result["product"]][result["account"]]["sum_ri_cost"] = result["sum_ri_cost"]

    #     f.write(result["product"]+","+result["account"]+","+result["sum_od_cost"]+","+result["sum_ri_cost"]+"\n")

    # f.close()
    return results


# def getaaa(table_name,database,s3_bucket):
#     # query_sql = "select * from test_jayhuang_cur limit 2"
#     query_sql = ("""
#         WITH 
#         results AS ( 
#         SELECT 
#         date_format(line_item_usage_start_date, '%M %Y') billing_date 
#         , date(line_item_usage_end_date) as billing_end_date 
#         , product_region 
#         , line_item_usage_account_id 
#         , product_instance_type 
#         , product_database_engine 
#         , line_item_usage_type 
#         , product_deployment_option 
#         , sum(line_item_unblended_cost) on_demand_cost 
#         , sum((CASE WHEN (line_item_line_item_description LIKE '%reserved instance applied%') THEN line_item_usage_amount ELSE 0 END)) reservation_covered_hours 
#         , sum((CASE WHEN (line_item_line_item_description LIKE '%instance hour (or partial hour)%' OR line_item_line_item_description LIKE '%running%') THEN CAST(line_item_usage_amount AS double) ELSE 0 END)) on_demand_hours 
#         FROM """+table_name+""" 
#         WHERE line_item_product_code LIKE 
#         '%"""+service_name+"""%' 
#         -- '%RDS%' 
#         AND line_item_usage_end_date between date('"""+start_date+"""') and date('"""+end_date+"""') 
#         AND line_item_usage_account_id in 
#         ('038528481xx4' ,'1380461xx805','1678xx136631') 
#         AND (line_item_line_item_description LIKE '%reserved instance applied%' OR line_item_line_item_description LIKE '%instance hour (or partial hour)%' OR line_item_line_item_description LIKE '%running%') 
#         GROUP BY 1, 2, 3, 4, 5, 6, 7, 8 
#         ) 
#         ,results_b AS ( 
#         SELECT 
#         results.product_region, 
#         results.line_item_usage_account_id , 
#         sum(results.on_demand_hours) as on_demand_hours, 
#         sum(results.reservation_covered_hours) as reservation_covered_hours, 
#         sum(results.on_demand_cost) as on_demand_cost 
#         FROM 
#         results 
#         group by 1,2 
#         ) 
#         -- final coverage rate count 
#         SELECT 
#         results_b.product_region, 
#         results_b.line_item_usage_account_id as Linked_AccountID , 
#         results_b.reservation_covered_hours, 
#         results_b.on_demand_hours, 
#         Cast((CASE WHEN results_b.reservation_covered_hours = 0 THEN 0 WHEN results_b.on_demand_hours = 0 THEN 100.0 ELSE (results_b.reservation_covered_hours / (results_b.reservation_covered_hours + results_b.on_demand_hours))*100 END) as int) "coverage (%)", 
#         cast(results_b.on_demand_cost as int) as "on_demand_cost ($)" 
#         FROM 
#         results_b 
#         ORDER BY 4 ASC
#         """)

   

    results = run_query(query_sql,database,s3_bucket)
    # print(results)
    # for result in results:
    #     print(result['identity_line_item_id'])
    # for result in results:
    #     if result["product"] not in ri_detail:
    #         ri_detail[result["product"]] = {}
        
    #     if result["account"] not in ri_detail[result["product"]]:
    #         ri_detail[result["product"]][result["account"]] = {}

    #     ri_detail[result["product"]][result["account"]]["sum_od_cost"] = result["sum_od_cost"]
    #     ri_detail[result["product"]][result["account"]]["sum_ri_cost"] = result["sum_ri_cost"]

    #     f.write(result["product"]+","+result["account"]+","+result["sum_od_cost"]+","+result["sum_ri_cost"]+"\n")

    # f.close()
    return results


def getLinkedAcct_RISP_purchased(table_name,database,s3_bucket,LinkedAccount_string, purchaseOpt):
    # query_sql = "select * from test_jayhuang_cur limit 2"
    # print(f"getLinkedAcct_RI_coverage LinkedAccount_string: {LinkedAccount_string}")
    
    query_sql = ("""
        SELECT DISTINCT
        a."purchase_option"
        ,(CASE WHEN (a."purchase_option" = 'Reserved') THEN concat(a."purchase_option",' ',a.service,' ',b.ri_sp_offering) WHEN (a."purchase_option" = 'SavingsPlan') THEN concat(a."purchase_option",' ',b.ri_sp_offering) ELSE 'NA' END) "ri_sp_type"
        , a."ri_sp_arn_mapping"
        ,  "a"."billing_period_mapping"
        , "a"."payer_account_id_mapping"
        , "a"."linked_account_id_mapping" as Linked_AccountID
        , "a"."instance_type"
        , "a"."ri_sp_end_date"
        , "b"."ri_sp_term"
        , "b"."ri_sp_offering"
        , "b"."ri_sp_payment"
        FROM
        (   (
            SELECT DISTINCT
            "bill_billing_period_start_date" "billing_period_mapping"
            , "bill_payer_account_id" "payer_account_id_mapping"
            , "line_item_usage_account_id" "Linked_account_id_mapping"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_savings_plan_a_r_n" WHEN ("reservation_reservation_a_r_n" <> '') THEN "reservation_reservation_a_r_n" ELSE '' END) "ri_sp_arn_mapping"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN CAST("from_iso8601_timestamp"("savings_plan_end_time") AS timestamp) WHEN (("reservation_reservation_a_r_n" <> '') AND ("reservation_end_time" <> '')) THEN CAST("from_iso8601_timestamp"("reservation_end_time") AS timestamp) ELSE null END) "ri_sp_end_date"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN 'SavingsPlan' WHEN ("reservation_reservation_a_r_n" <> '') THEN 'Reserved' WHEN ("line_item_usage_type" LIKE '%Spot%') THEN 'Spot' ELSE 'OnDemand' END) "purchase_option"
            , (CASE WHEN ("line_item_product_code" = 'AWSElementalMediaLive') THEN "split_part"("line_item_line_item_description", 'reserved', 2) WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN product_instance_type ELSE "split_part"("line_item_line_item_description", ',', 2) END) "instance_type"
            , (CASE WHEN (("bill_billing_entity" = 'AWS Marketplace') AND (NOT ("line_item_line_item_type" LIKE '%Discount%'))) THEN "Product_Product_Name" WHEN ("product_servicecode" = '') THEN "line_item_product_code" ELSE "product_servicecode" END) "service"
            FROM
                """+table_name+""" 
            WHERE (("line_item_line_item_type" = 'RIFee') OR ("line_item_line_item_type" = 'SavingsPlanRecurringFee'))
            )  a
            LEFT JOIN (
            SELECT DISTINCT
                "bill_billing_period_start_date" "billing_period_mapping"
            , "bill_payer_account_id" "payer_account_id_mapping"
            , "line_item_usage_account_id" "Linked_account_id_mapping"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_savings_plan_a_r_n" WHEN ("reservation_reservation_a_r_n" <> '') THEN "reservation_reservation_a_r_n" ELSE '' END) "ri_sp_arn_mapping"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_purchase_term" WHEN ("reservation_reservation_a_r_n" <> '') THEN "pricing_lease_contract_length" ELSE '' END) "ri_sp_term"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_offering_type" WHEN ("reservation_reservation_a_r_n" <> '') THEN "pricing_offering_class" ELSE '' END) "ri_sp_offering"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_payment_option" WHEN ("reservation_reservation_a_r_n" <> '') THEN "pricing_purchase_option" ELSE '' END) "ri_sp_Payment"
            , (CASE WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN 'SavingsPlan' WHEN ("reservation_reservation_a_r_n" <> '') THEN 'Reserved' WHEN ("line_item_usage_type" LIKE '%Spot%') THEN 'Spot' ELSE 'OnDemand' END) "purchase_option"
            , (CASE WHEN ((("line_item_usage_type" LIKE '%Spot%') AND ("line_item_product_code" = 'AmazonEC2')) AND ("line_item_line_item_type" = 'Usage')) THEN "split_part"("line_item_line_item_description", ' ', 1) ELSE "product_instance_type" END) "instance_type"
            FROM
                """+table_name+""" 
            -- WHERE (("line_item_line_item_type" = 'DiscountedUsage') OR ("line_item_line_item_type" = 'SavingsPlanCoveredUsage'))
            )  b ON ( (("a"."ri_sp_arn_mapping" = "b"."ri_sp_arn_mapping") AND ("a"."billing_period_mapping" = "b"."billing_period_mapping")) AND ("a"."linked_account_id_mapping" = "b"."linked_account_id_mapping") AND ("a"."payer_account_id_mapping" = "b"."payer_account_id_mapping"))
        )
        WHERE ("a"."billing_period_mapping" >= "date"('2023-10-01')) and ("a"."ri_sp_end_date" >= current_date) 
        and "a"."linked_account_id_mapping" in """+LinkedAccount_string+"""
        and "a"."purchase_option" = '"""+purchaseOpt+"""'
        order by "ri_sp_type","a"."ri_sp_arn_mapping","a"."ri_sp_end_date","a"."linked_account_id_mapping"

        """)

    print(f"377 query_sql: {query_sql}")

    results = run_query(query_sql,database,s3_bucket)
    print(results)
    return results
