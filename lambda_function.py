import json
import os
import urllib.parse
import urllib.request

# from awsCUR import getLinkedAcct_SP_usage, getLinkedAcct_RI_coverage
import awsCUR
from awsCostExplorer import getSavingsPlansUtilization, getSavingsPlansUtilizationRecommendation, getSavingsPlansEC2UtilizationRecommendation, getReservationPurchaseRecommendation
from awsSavingsPlans import getSavingsPlans


import datetime

import boto3

from io import StringIO
import xlsxwriter

# configuration for s3
REPORT_BUCKET_NAME = "customer-aws-ri-sp-recommendation" # output report destination s3 bucket
PARAMETER_PATH = "customer-account-list.csv" # your report account list in report s3 bucket
# configuration for Athena
ATHENA_QUERY_RESULT_S3_BUCKET = 'aws-cur-athena-query-results-us-east-1'  # Query result s3 bucket @ N. virginia
CUR_DATABASE_NAME  = 'athenacurcfn_cur_report'  
CUR_TABLE_NAME = 'cur_report' 

DELTA_DAYS = 60

s3 = boto3.client('s3')

def send_slack(title,path):
    
    item = {}

    item['color'] = '#36a64f'
    item['title'] = title
    item['fields'] = [{'title': 'Path', 'value': path}]

    print(item)

    attachments=[item]

    channel="GAGxxTQMT" #customer slack channel ID
    channel=urllib.parse.quote(channel)
    token="xoxb-2169638328-612809098273-142JkMmLpkszSNmuxxxxxx"
    attachments=urllib.parse.quote(json.dumps(attachments))
    slack_cmd ="curl -X POST \"https://slack.com/api/chat.postMessage?token=%s&channel=%s&attachments=%s&pretty=1\""%(token,channel,attachments)
    
    os.system(slack_cmd)

def lambda_handler(event, context):
    # TODO implement
    print("start step1")
        
    linked_account_list = []
    results = {}
    start_date = (datetime.datetime.now() - datetime.timedelta(days = 60)).strftime("%Y-%m-%d")
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # step 0. get account list
    account_list_file = s3.get_object(Bucket= REPORT_BUCKET_NAME , Key = PARAMETER_PATH)
    account_list_file_lines = account_list_file['Body'].read().splitlines()
    print('63 ===> account_list_file.read():', account_list_file_lines)
    
    
    for line in account_list_file_lines:
        each_line = line.decode('utf-8').split(",")
        linked_account = each_line[0]
        account_name = each_line[1]
        print('70 ===> @@account_name',account_name)
        
        linked_account_list.append(linked_account)
        results[linked_account] = {}
        results[linked_account]["name"] = account_name
        results[linked_account]["totalHourlyCommitment"] = None
        results[linked_account]["HourlyCommitmentToPurchase"] = None
        results[linked_account]["EstimatedSavingsAmount"] = None
        results[linked_account]["EstimatedSavingsPercentage"] = None
        results[linked_account]["totalSpend_SP_covered"] = None
        results[linked_account]["totalSpend_OD_covered"] = None
        results[linked_account]["coverage"] = None
   
    LinkedAccount_string = "('" + "','".join(linked_account_list) + "')"
    # print(f"LinkedAccount_string: {LinkedAccount_string}")
    
    ###########
    # sheet 1  
    # compute-sp-recommendation
    # #######
    # 
    # step 1.	Gen Customer CUR report for SP usage by Athena
    response_1 = awsCUR.getLinkedAcct_SP_usage(CUR_TABLE_NAME, CUR_DATABASE_NAME, ATHENA_QUERY_RESULT_S3_BUCKET, str(DELTA_DAYS),start_date,end_date,LinkedAccount_string)
    # print(f'SP usage: {response_1}')
    
    if response_1 is None:
        print("SP usage no data")
    else:
        for record in response_1:
            linked_account = record["LinkedAccount"]
            if linked_account not in linked_account_list:
                linked_account_list.append(linked_account)
                results[linked_account]={}
                results[linked_account]["name"] = ""
                results[linked_account]["totalHourlyCommitment"] = 0
                results[linked_account]["HourlyCommitmentToPurchase"] = None
                results[linked_account]["EstimatedSavingsAmount"] = None
                results[linked_account]["EstimatedSavingsPercentage"] = None
                results[linked_account]["totalSpend_SP_covered"] = None
                results[linked_account]["totalSpend_OD_covered"] = None
                results[linked_account]["coverage"] = None
    
            results[linked_account]["totalSpend_SP_covered"] = record["totalSpend_SP_covered"]
            results[linked_account]["totalSpend_OD_covered"] = record["totalSpend_OD_covered"]
            results[linked_account]["coverage"] = record["coverage (%)"]
          
    
    
    
    # step 3.	Copy the sp_usage , od_cost and coverage rate to “kks-linkedAccount-SP-coverage-60d-final template”
    current_datetime = datetime.datetime.now()
    sixty_days_ago = current_datetime - datetime.timedelta(days=DELTA_DAYS)
    end_date = current_datetime.strftime("%Y-%m-%d")
    start_date = sixty_days_ago.strftime("%Y-%m-%d")
    
    print(f"Recommand Period >> Start Date: {start_date} - End Date: {end_date}")

    for acct in linked_account_list:      
        response = getSavingsPlansUtilization(datetime.date.today().strftime("%Y-%m")+'-01',datetime.date.today().strftime("%Y-%m")+'-02' ,acct)
        # print(f'getSavingsPlansUtilization: {response}')
        if response is not None and 'SavingsPlansUtilizationsByTime' in response:
            results[acct]["totalHourlyCommitment"] = round(float(response['SavingsPlansUtilizationsByTime'][0]['Utilization']['TotalCommitment'])/24, 2)
    # response_3 = getSavingsPlansUtilization(start_date,end_date)
    
    # response = getSavingsPlansUtilizationRecommendation('2021-04-01','2021-06-01')
    # response_3 = getSavingsPlans()
    
    # if response_3:
    #     # print(response_3)
    #     for record in response_3['savingsPlans']:
    #         linked_account = record["savingsPlanArn"].split("savingsplans::")[1].split(":savingsplan/")[0]
        
    #         if linked_account not in linked_account_list:
    #             linked_account_list.append(linked_account)
    #             results[linked_account]={}
    #             results[linked_account]["name"] = ""
    #             results[linked_account]["totalHourlyCommitment"] = 0
    #             results[linked_account]["HourlyCommitmentToPurchase"] = None
    #             results[linked_account]["EstimatedSavingsAmount"] = None
    #             results[linked_account]["EstimatedSavingsPercentage"] = None
    #             results[linked_account]["totalSpend_SP_covered"] = None
    #             results[linked_account]["totalSpend_OD_covered"] = None
    #             results[linked_account]["coverage"] = None
        
                
    #         results[linked_account]["totalHourlyCommitment"] = results[linked_account]["totalHourlyCommitment"] + float(record['commitment'])
    
    # step 3-2)	Download the recommendation for Compute Savings Plans and past the column to template. 
    response_3_2 = getSavingsPlansUtilizationRecommendation()
    # print("response_3_2")
    # print(response_3_2)
    if response_3_2 is not None and 'SavingsPlansPurchaseRecommendationDetails' in response_3_2:
        for record in response_3_2['SavingsPlansPurchaseRecommendation']['SavingsPlansPurchaseRecommendationDetails']:
            linked_account = record["AccountId"]
        
            if linked_account not in linked_account_list:
                linked_account_list.append(linked_account)
                results[linked_account]={}
                results[linked_account]["name"] = ""
                results[linked_account]["totalHourlyCommitment"] = None
                results[linked_account]["HourlyCommitmentToPurchase"] = None
                results[linked_account]["EstimatedSavingsAmount"] = None
                results[linked_account]["EstimatedSavingsPercentage"] = None
                results[linked_account]["totalSpend_SP_covered"] = None
                results[linked_account]["totalSpend_OD_covered"] = None
                results[linked_account]["coverage"] = None
                
            results[linked_account]["HourlyCommitmentToPurchase"] = float(record['HourlyCommitmentToPurchase'])
            results[linked_account]["EstimatedSavingsAmount"] = float(record['EstimatedSavingsAmount'])
            results[linked_account]["EstimatedSavingsPercentage"] = float(record['EstimatedSavingsPercentage'])
            
        # print(results)
    print('182 ===> getSavingsPlansUtilizationRecommendation, linked_account_list =', linked_account_list)
    
    # generate XLSX report
    
    workbook = xlsxwriter.Workbook('/tmp/customer-linkedAccount-RI&SP-recommendation.xlsx')
    worksheet = workbook.add_worksheet('compute-sp-recommendation')
    
    hf_0 = workbook.add_format({'text_wrap':True})
    
    hf_1 = workbook.add_format({'text_wrap':True})
    hf_1.set_bg_color('#BDEDC9')
    hf_1.set_border()
    
    hf_2 = workbook.add_format({'text_wrap':True})
    hf_2.set_bg_color('#D7E8F5')
    hf_2.set_border()
    
    
    
    cf_0 = workbook.add_format()
    
    cf_1 = workbook.add_format()
    cf_1.set_bg_color('#BDEDC9')
    cf_1.set_border()
    
    cf_2 = workbook.add_format()
    cf_2.set_bg_color('#D7E8F5')
    cf_2.set_border()
    
    worksheet.set_column(0, 0, 12)
    worksheet.set_column(1, 1, 15)
    worksheet.set_column(2, 2, 10)
    worksheet.set_column(3, 3, 10)
    worksheet.set_column(4, 4, 10)
    worksheet.set_column(5, 5, 10)
    worksheet.set_column(6, 6, 10)
    worksheet.set_column(7, 7, 10)
    worksheet.set_column(8, 8, 10)
    
    
    xlsx_header = ["Account ID","Account Name","Current totalHourly Commitment","Current Sum of spend_covered_by_sp ($)(60days)","Current Sum of od_cost ($)(60days)","Current Sum of coverage (60days) (%)","Recommand Hourly commitment to purchase (60days)","Estimated monthly savings amount ($)","Estimated savings percentage (%)"]
    header_format = [hf_0,hf_0,hf_1,hf_2,hf_2,hf_2,hf_1,hf_0,hf_0]
    data_key = ["name","totalHourlyCommitment","totalSpend_SP_covered","totalSpend_OD_covered","coverage","HourlyCommitmentToPurchase","EstimatedSavingsAmount","EstimatedSavingsPercentage"]
    data_format = [cf_0,cf_1,cf_0,cf_0,cf_1,cf_1,cf_0,cf_0]
    row = 0
    col = 0
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet.write(row, col, header,header_format[col])
        col += 1
    
    row +=1
    
    print('235===> linked_account_list =', linked_account_list)
    for acct in linked_account_list:
        col = 0
        worksheet.write(row, col, acct,data_format[col])
        col += 1
        # print('239===> acct=',acct)
        # print('239===> results[acct] =', results[acct])
        for key in data_key:
            worksheet.write(row,col,results[acct][key])
            col += 1
        row +=1        
    
    ###########
    # sheet 2 
    # ec2_sp_recommendation sheet 
    # #######
    # 
    
    # step 0. get account list
    
    # for line in account_list_file['Body'].read().splitlines():
    #     each_line = line.decode('utf-8').split(",")
    #     linked_account = each_line[0]
    #     account_name = each_line[1]
    
        # linked_account_list.append(linked_account)

    for linked_account in linked_account_list:
        account_name = results[linked_account]["name"]
        results[linked_account] = {}
        results[linked_account]["name"] = account_name
        results[linked_account]["instance_family_list"] = []
    


    # step 3-2)	Download the recommendation for Compute Savings Plans and past the column to template. 
    response_3_2 = getSavingsPlansEC2UtilizationRecommendation()
    # print("response_3_2")
    # print(response_3_2)
    
    if response_3_2 is not None and 'SavingsPlansPurchaseRecommendationDetails' in response_3_2:
        for record in response_3_2['SavingsPlansPurchaseRecommendation']['SavingsPlansPurchaseRecommendationDetails']:
            linked_account = record["AccountId"]
            instance_family = record["SavingsPlansDetails"]["InstanceFamily"]
        
            if linked_account not in linked_account_list:
                linked_account_list.append(linked_account)
                results[linked_account]={}
                results[linked_account]["name"] = ""
                results[linked_account]["instance_family_list"] = []
            if instance_family not in results[linked_account]["instance_family_list"]:
                results[linked_account]["instance_family_list"].append(instance_family)
                results[linked_account][instance_family] = {}
        
            # results[linked_account]["name"] = account_name
            results[linked_account][instance_family]["HourlyCommitmentToPurchase"] = float(record['HourlyCommitmentToPurchase'])
            results[linked_account][instance_family]["EstimatedSavingsAmount"] = float(record['EstimatedSavingsAmount'])
            results[linked_account][instance_family]["EstimatedSavingsPercentage"] = float(record['EstimatedSavingsPercentage'])
        
    # print('291 ===> getSavingsPlansEC2UtilizationRecommendation, linked_account_list =', linked_account_list)    
    
    # generate XLSX report
    
    worksheet2 = workbook.add_worksheet('ec2_sp_recommendation')
    
     
    
    worksheet2.set_column(0, 0, 12)
    worksheet2.set_column(1, 1, 15)
    worksheet2.set_column(2, 2, 10)
    worksheet2.set_column(3, 3, 10)
    worksheet2.set_column(4, 4, 10)
    worksheet2.set_column(5, 5, 10)
    worksheet2.set_column(6, 6, 10)
    worksheet2.set_column(7, 7, 10)
    worksheet2.set_column(8, 8, 10)
    
    
    xlsx_header = ["Account ID","Account Name","Instance Family","Hourly Commitment to Purchase", "Estimated monthly savings amount", "Estimated monthly saving percentage"]
    header_format = [hf_0,hf_0,hf_1,hf_2,hf_2,hf_2]
    # data_key = ["name","totalHourlyCommitment","InstanceFamily","EstimatedMonthlySavingsAmount","coverage","HourlyCommitmentToPurchase","EstimatedSavingsAmount","EstimatedSavingsPercentage"]
    # data_format = [cf_0,cf_1,cf_0,cf_0,cf_1,cf_1,cf_0,cf_0]
    row = 0
    col = 0
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet2.write(row, col, header,header_format[col])
        col += 1
    
    row +=1
    
    
    for acct in linked_account_list:
        for instance_family in results[acct]["instance_family_list"]:
    
            worksheet2.write(row, 0, acct)
            worksheet2.write(row, 1, results[acct]["name"])
            worksheet2.write(row, 2, instance_family)
            worksheet2.write(row, 3, results[acct][instance_family]["HourlyCommitmentToPurchase"])
            worksheet2.write(row, 4, results[acct][instance_family]["EstimatedSavingsAmount"])
            worksheet2.write(row, 5, results[acct][instance_family]["EstimatedSavingsPercentage"])
    
            row +=1         
    
    #####
    # part 3 
    # elasticache-ri-recommendation sheet
    ####
    
       
    # # step 0. get account list
    
    # for line in account_list_file['Body'].read().splitlines():
    #     each_line = line.decode('utf-8').split(",")
    #     linked_account = each_line[0]
    #     account_name = each_line[1]
    
    #     linked_account_list.append(linked_account)

    for linked_account in linked_account_list:
        account_name = results[linked_account]["name"]
        results[linked_account] = {}
        results[linked_account]["name"] = account_name
        results[linked_account]["instance_family_list"] = []
    
    ri_hf_1 = workbook.add_format()
    # cf_1.set_pattern(1)  # This is optional when using a solid fill.
    ri_hf_1.set_bg_color('#F7CC9E')
    ri_hf_1.set_border()
    
    # workbook = xlsxwriter.Workbook('elasticache-ri-recommendation.xlsx')
    worksheet3 = workbook.add_worksheet('elasticache-ri-recommendation')
    
    
    worksheet3.set_column(0, 0, 12)
    worksheet3.set_column(1, 1, 15)
    worksheet3.set_column(2, 2, 10)
    worksheet3.set_column(3, 3, 10)
    worksheet3.set_column(4, 4, 10)
    worksheet3.set_column(5, 5, 10)
    worksheet3.set_column(6, 6, 10)
    worksheet3.set_column(7, 7, 10)
    worksheet3.set_column(8, 8, 10)
    
    xlsx_header = [
        "Recommendation Date",
        "Account ID",
        "Account Name",
        # "Instance Type (Unit)"
        "Projected RI Utilization(%)",
        "Node Type", 
        "Recommended Instance Quantity Purchase",
        "Recommended Normalized Unit Quantity Purchase",
        "Cache Engine",
        "Estimated Monthly Savings ($)",
        "Break Even Months ($)"]
    
    row = 0
    col = 0
    
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet3.write(row, col, header,ri_hf_1)
        col += 1
    
    row +=1
    
    # step 3-2)	Download the recommendation for Compute Savings Plans and past the column to template. 
    # Amazon Elastic Compute Cloud - Compute, Amazon Relational Database Service, Amazon Redshift, Amazon ElastiCache, Amazon Elasticsearch Service
    response_3_2 = getReservationPurchaseRecommendation("Amazon ElastiCache")
    # print("403====> response_3_2")
    # print(response_3_2['Recommendations'])
    
    report_record = []
    if len(response_3_2['Recommendations']) >0:
        for record in response_3_2['Recommendations'][0]['RecommendationDetails']: 
            linked_account = record["AccountId"]
            
            # if the linked account not in the assigned list then skip to write into worksheet:
            if linked_account not in linked_account_list:
                print(f'421==> {linked_account} not in linked_account_list')
                continue
                # results[linked_account]["name"] = ""
            
            worksheet3.write(row, 0, response_3_2['Metadata']['GenerationTimestamp'])
            worksheet3.write(row, 1, linked_account)
            #if linked_account in results:
            worksheet3.write(row, 2, results[linked_account]["name"])
            #else:
            #    worksheet3.write(row, 2, "")
            worksheet3.write(row, 3, record["AverageUtilization"])
            worksheet3.write(row, 4, record["InstanceDetails"]["ElastiCacheInstanceDetails"]["NodeType"])
            worksheet3.write(row, 5, record["RecommendedNumberOfInstancesToPurchase"])
            worksheet3.write(row, 6, record["RecommendedNormalizedUnitsToPurchase"])
            worksheet3.write(row, 7, record["InstanceDetails"]["ElastiCacheInstanceDetails"]["ProductDescription"])
            worksheet3.write(row, 8, record["EstimatedMonthlySavingsAmount"])
            worksheet3.write(row, 9, record["EstimatedBreakEvenInMonths"])
            row +=1  
    
    ########
    # part 4
    # rds-ri-recommendation sheet
    #######
    
 
    # step 0. get account list
    
    # for line in account_list_file['Body'].read().splitlines():
    #     each_line = line.decode('utf-8').split(",")
    #     linked_account = each_line[0]
    #     account_name = each_line[1]
    
    #     linked_account_list.append(linked_account)

    for linked_account in linked_account_list:
        account_name = results[linked_account]["name"]
        results[linked_account] = {}
        results[linked_account]["name"] = account_name
        results[linked_account]["instance_family_list"] = []
    
    
    
    # workbook = xlsxwriter.Workbook('rds-ri-recommendation.xlsx')
    worksheet4 = workbook.add_worksheet('rds-ri-recommendation')
    
    
    worksheet4.set_column(0, 0, 12)
    worksheet4.set_column(1, 1, 15)
    worksheet4.set_column(2, 2, 10)
    worksheet4.set_column(3, 3, 10)
    worksheet4.set_column(4, 4, 10)
    worksheet4.set_column(5, 5, 10)
    worksheet4.set_column(6, 6, 10)
    worksheet4.set_column(7, 7, 10)
    worksheet4.set_column(8, 8, 10)
    
    xlsx_header = [
        "Recommendation Date",
        "Account ID",
        "Account Name",
        # "Instance Type (Unit)"
        "Projected RI Utilization(%)",
        "Database Engine", 
        "Recommended Instance Quantity Purchase",
        "Recommended Normalized Unit Quantity Purchase",
        "Instance Type",
        "Estimated Monthly Savings ($)",
        "Break Even Months ($)"]
    
    row = 0
    col = 0
    
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet4.write(row, col, header,ri_hf_1)
        col += 1
    
    row +=1
    
    # step 3-2)	Download the recommendation for RI  and past the column to template. 
    # Amazon Elastic Compute Cloud - Compute, Amazon Relational Database Service, Amazon Redshift, Amazon ElastiCache, Amazon Elasticsearch Service
    response_3_2 = getReservationPurchaseRecommendation("Amazon Relational Database Service")
    # print("494 ====> response_3_2")
    # print(response_3_2['Recommendations'])
    
    report_record = []
    ### sample output
    if len(response_3_2['Recommendations']) >0:
        for record in response_3_2['Recommendations'][0]['RecommendationDetails']:
            linked_account = record["AccountId"]
            
            # if the linked account not in the assigned list then skip to write into worksheet:
            if linked_account not in linked_account_list:
                print(f'503==> {linked_account} not in linked_account_list')
                continue
                # results[linked_account]["name"] = ""
    
            
            # instance_family = record["SavingsPlansDetails"]["InstanceFamily"]
            worksheet4.write(row, 0, response_3_2['Metadata']['GenerationTimestamp'])
            worksheet4.write(row, 1, linked_account)
            #if linked_account in results:
            worksheet4.write(row, 2, results[linked_account]["name"])
            #else:
            #    worksheet4.write(row, 2, "")
            worksheet4.write(row, 3, record["AverageUtilization"])
            worksheet4.write(row, 4, record["InstanceDetails"]["RDSInstanceDetails"]["DatabaseEngine"])
            worksheet4.write(row, 5, record["RecommendedNumberOfInstancesToPurchase"])
            worksheet4.write(row, 6, record["RecommendedNormalizedUnitsToPurchase"])
            worksheet4.write(row, 7, record["InstanceDetails"]["RDSInstanceDetails"]["InstanceType"])
            worksheet4.write(row, 8, record["EstimatedMonthlySavingsAmount"])
            worksheet4.write(row, 9, record["EstimatedBreakEvenInMonths"])
        
            row +=1  
        
    
    #######
    # part 5 
    # ri-ec-coverage sheet
    #######
    
    
    # linked_account_list = []
    # results = {}
    
    # # step 0. get account list
    
    # for line in account_list_file['Body'].read().splitlines():
    #     each_line = line.decode('utf-8').split(",")
    #     linked_account = each_line[0]
    #     account_name = each_line[1]
    
    #     linked_account_list.append(linked_account)

    for linked_account in linked_account_list:
        account_name = results[linked_account]["name"]
        results[linked_account] = {}
        results[linked_account]["name"] = account_name
        results[linked_account]["product_region"] = None
        results[linked_account]["reservation_covered_hours"] = None
        results[linked_account]["on_demand_hours"] = None
        results[linked_account]["coverage (%)"] = None
        results[linked_account]["on_demand_cost ($)"] = None
    
    
    # step 1.	Gen Customer CUR report for SP usage by Athena # 
    response_1 = awsCUR.getLinkedAcct_RI_coverage(CUR_TABLE_NAME, CUR_DATABASE_NAME, ATHENA_QUERY_RESULT_S3_BUCKET, str(DELTA_DAYS), "AmazonElastiCache",start_date,end_date,LinkedAccount_string)
    # print(response_1)

    # # step 3-2)	Download the coverage for Reserved Instance(RI) and past the column to template. 
    # # Retrieves the reservation coverage for your account, which you can use to see how much of your Amazon Elastic Compute Cloud, Amazon ElastiCache, Amazon Relational Database Service, or Amazon Redshift usage is covered by a reservation.
    # response_3_2 = getRICoverageByLinkedAccount(start_date, end_date,"Amazon ElastiCache", linked_account_list)
    # print("AmazonElastiCache coverage response_3_2")
    # print(response_3_2)
    
    if response_1 is None:
        print("AmazonElastiCache coverage no data")
    else:
        for record in response_1:
            linked_account = record["Linked_AccountID"]
            if linked_account not in linked_account_list:
                linked_account_list.append(linked_account)
                results[linked_account]={}
                results[linked_account]["name"] = ""
                results[linked_account]["product_region"] = None
                results[linked_account]["reservation_covered_hours"] = None
                results[linked_account]["on_demand_hours"] = None
                results[linked_account]["coverage (%)"] = None
                results[linked_account]["on_demand_cost ($)"] = None
    
    
            # results[linked_account]["name"] = account_name
            results[linked_account]["product_region"] = record["product_region"]
            results[linked_account]["reservation_covered_hours"] = record["reservation_covered_hours"]
            results[linked_account]["on_demand_hours"] = record["on_demand_hours"]
            results[linked_account]["coverage (%)"] = record["coverage (%)"]
            results[linked_account]["on_demand_cost ($)"] = record["on_demand_cost ($)"]
            
    
    
    
    # generate XLSX report
    
    # workbook = xlsxwriter.Workbook('ri-ec-coverage.xlsx')
    worksheet5 = workbook.add_worksheet('ri-ec-coverage')
    
    
    worksheet5.set_column(0, 0, 12)
    worksheet5.set_column(1, 1, 15)
    worksheet5.set_column(2, 2, 10)
    worksheet5.set_column(3, 3, 10)
    worksheet5.set_column(4, 4, 10)
    worksheet5.set_column(5, 5, 10)
    worksheet5.set_column(6, 6, 10)
    worksheet5.set_column(7, 7, 10)
    worksheet5.set_column(8, 8, 10)
    
    xlsx_header = ["Account ID","Account Name","Product Region", "reservation_covered_hours", "On Demand Hours", "Coverage (%)", "On Demand Cost ($)"]
    data_key = ["name","product_region","reservation_covered_hours","on_demand_hours","coverage (%)", "on_demand_cost ($)"]
    row = 0
    col = 0
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet5.write(row, col, header,ri_hf_1)
        col += 1
    
    row +=1
    
    
    for acct in linked_account_list:
        col = 0
        worksheet5.write(row, col, acct)
        col += 1
        for key in data_key:
            worksheet5.write(row,col,results[acct][key])
            col += 1
        row +=1        
        print(results[acct])
    
    #######
    # part 6
    # ri-rds-coverage sheet
    #######
    
    
    # linked_account_list = []
    # results = {}
    
    # # step 0. get account list
    
    # for line in account_list_file['Body'].read().splitlines():
    #     each_line = line.decode('utf-8').split(",")
    #     linked_account = each_line[0]
    #     account_name = each_line[1]
    
    #     linked_account_list.append(linked_account)

    for linked_account in linked_account_list:
        account_name = results[linked_account]["name"]
        results[linked_account] = {}
        results[linked_account]["name"] = account_name
        results[linked_account]["product_region"] = None
        results[linked_account]["reservation_covered_hours"] = None
        results[linked_account]["on_demand_hours"] = None
        results[linked_account]["coverage (%)"] = None
        results[linked_account]["on_demand_cost ($)"] = None
    
    
    # step 1.	Gen Customer CUR report for SP usage by Athena # AmazonElastiCache
    response_1 = awsCUR.getLinkedAcct_RI_coverage(CUR_TABLE_NAME, CUR_DATABASE_NAME, ATHENA_QUERY_RESULT_S3_BUCKET, str(DELTA_DAYS), "RDS",start_date,end_date, LinkedAccount_string)
    # print(response_1)
       
    if response_1 is None:
        print("RDS coverage no data")
    else:
        for record in response_1:
            linked_account = record["Linked_AccountID"]
            if linked_account not in linked_account_list:
                linked_account_list.append(linked_account)
                results[linked_account]={}
                results[linked_account]["name"] = ""
                results[linked_account]["product_region"] = None
                results[linked_account]["reservation_covered_hours"] = None
                results[linked_account]["on_demand_hours"] = None
                results[linked_account]["coverage (%)"] = None
                results[linked_account]["on_demand_cost ($)"] = None
    
            # results[linked_account]["name"] = account_name
            results[linked_account]["product_region"] = record["product_region"]
            results[linked_account]["reservation_covered_hours"] = record["reservation_covered_hours"]
            results[linked_account]["on_demand_hours"] = record["on_demand_hours"]
            results[linked_account]["coverage (%)"] = record["coverage (%)"]
            results[linked_account]["on_demand_cost ($)"] = record["on_demand_cost ($)"]
           
    
    # generate XLSX report
    
    # workbook = xlsxwriter.Workbook('ri-rds-coverage.xlsx')
    worksheet6 = workbook.add_worksheet('ri-rds-coverage')
    
    
    worksheet6.set_column(0, 0, 12)
    worksheet6.set_column(1, 1, 15)
    worksheet6.set_column(2, 2, 10)
    worksheet6.set_column(3, 3, 10)
    worksheet6.set_column(4, 4, 10)
    worksheet6.set_column(5, 5, 10)
    worksheet6.set_column(6, 6, 10)
    worksheet6.set_column(7, 7, 10)
    worksheet6.set_column(8, 8, 10)
    
    xlsx_header = ["Account ID","Account Name","Product Region", "reservation_covered_hours", "On Demand Hours", "Coverage (%)", "On Demand Cost ($)"]
    data_key = ["name","product_region","reservation_covered_hours","on_demand_hours","coverage (%)","on_demand_cost ($)"]
    row = 0
    col = 0
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet6.write(row, col, header,ri_hf_1)
        col += 1
    
    row +=1
    
    
    for acct in linked_account_list:
        col = 0
        worksheet6.write(row, col, acct)
        col += 1
        for key in data_key:
            worksheet6.write(row,col,results[acct][key])
            col += 1
        row +=1        
        print(results[acct])
   
    #######
    # part 7
    # SP purchased sheet
    #######
     
    # generate XLSX report
    
    # workbook = xlsxwriter.Workbook('ri-rds-coverage.xlsx')
    worksheet7 = workbook.add_worksheet('sp-purchased')
    
    
    worksheet7.set_column(0, 0, 12)
    worksheet7.set_column(1, 1, 15)
    worksheet7.set_column(2, 2, 10)
    worksheet7.set_column(3, 3, 10)
    worksheet7.set_column(4, 4, 10)
    worksheet7.set_column(5, 5, 10)
    worksheet7.set_column(6, 6, 10)
    worksheet7.set_column(7, 7, 10)
    worksheet7.set_column(8, 8, 10)
    
    xlsx_header = ["Account ID","Account Name","RI/SP Type", "RI/SP resource arn", "RI/SP Expired Date", "Instance Type", "RI/SP Term", "RI/SP Payment"]
    data_key = ["name","ri_sp_type","ri_sp_arn","ri_sp_end_date","instance_type","ri_sp_term","ri_sp_payment"]
    row = 0
    col = 0
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet7.write(row, col, header,ri_hf_1)
        col += 1
    
    row +=1
    
    #step 3. Gen Customer CUR report for SP purchase by Athena 
    response_3 = awsCUR.getLinkedAcct_RISP_purchased(CUR_TABLE_NAME, CUR_DATABASE_NAME, ATHENA_QUERY_RESULT_S3_BUCKET,LinkedAccount_string, 'SavingsPlan')
    print(f'769==> response_3 = {response_3}')

    # report_record = []
    ### sample output
    if response_3 is None:
        print("SP purchased no data")
    else:
        for record in response_3:
            linked_account = record["Linked_AccountID"]
                   
            # if the linked account not in the assigned list then skip to write into worksheet:
            if linked_account not in linked_account_list:
                print(f'781==> {linked_account} not in linked_account_list')
                continue
                # results[linked_account]["name"] = ""
    
            worksheet7.write(row, 0, linked_account)
            worksheet7.write(row, 1, results[linked_account]["name"])
            worksheet7.write(row, 2, record["ri_sp_type"])
            worksheet7.write(row, 3, record["ri_sp_arn_mapping"])
            worksheet7.write(row, 4, record["ri_sp_end_date"])
            worksheet7.write(row, 5, record["instance_type"])
            worksheet7.write(row, 6, record["ri_sp_term"])
            worksheet7.write(row, 7, record["ri_sp_payment"])
        
            row +=1  
    
    #######
    # part 8
    # RI purchased sheet
    #######
     
    # generate XLSX report
    
    # workbook = xlsxwriter.Workbook('ri-rds-coverage.xlsx')
    worksheet8 = workbook.add_worksheet('ri-purchased')
    
    
    worksheet8.set_column(0, 0, 12)
    worksheet8.set_column(1, 1, 15)
    worksheet8.set_column(2, 2, 10)
    worksheet8.set_column(3, 3, 10)
    worksheet8.set_column(4, 4, 10)
    worksheet8.set_column(5, 5, 10)
    worksheet8.set_column(6, 6, 10)
    worksheet8.set_column(7, 7, 10)
    worksheet8.set_column(8, 8, 10)
    
    xlsx_header = ["Account ID","Account Name","RI/SP Type", "RI/SP resource arn", "RI/SP Expired Date", "Instance Type", "RI/SP Term", "RI/SP Payment"]
    data_key = ["name","ri_sp_type","ri_sp_arn","ri_sp_end_date","instance_type","ri_sp_term","ri_sp_payment"]
    row = 0
    col = 0
    
    for header in xlsx_header:
        print(str(col) + ", "+ header)
        worksheet8.write(row, col, header,ri_hf_1)
        col += 1
    
    row +=1


    #step 3. Gen Customer CUR report for SP purchase by Athena 
    response_3 = awsCUR.getLinkedAcct_RISP_purchased(CUR_TABLE_NAME, CUR_DATABASE_NAME, ATHENA_QUERY_RESULT_S3_BUCKET,LinkedAccount_string, 'Reserved')
    print(f'832==> response_3 = {response_3}')

    ### sample output
    if response_3 is None:
        print("RI purchased no data")
    else:
        for record in response_3:
            linked_account = record["Linked_AccountID"]
                   
            # if the linked account not in the assigned list then skip to write into worksheet:
            if linked_account not in linked_account_list:
                print(f'843==> {linked_account} not in linked_account_list')
                continue
                # results[linked_account]["name"] = ""
    
            worksheet8.write(row, 0, linked_account)
            worksheet8.write(row, 1, results[linked_account]["name"])
            worksheet8.write(row, 2, record["ri_sp_type"])
            worksheet8.write(row, 3, record["ri_sp_arn_mapping"])
            worksheet8.write(row, 4, record["ri_sp_end_date"])
            worksheet8.write(row, 5, record["instance_type"])
            worksheet8.write(row, 6, record["ri_sp_term"])
            worksheet8.write(row, 7, record["ri_sp_payment"])
        
            row +=1  

    
    ##End of Excel sheet
    workbook.close()

    #s3.upload_file('/tmp/customer-linkedAccount-RI&SP-recommendation.xlsx', REPORT_BUCKET_NAME,'customer-linkedAccount-RI&SP-recommendation.xlsx')
    s3.upload_file('/tmp/customer-linkedAccount-RI&SP-recommendation.xlsx',REPORT_BUCKET_NAME, 'customer-linkedAccount-RI&SP-recommendation-%s-%s.xlsx' % (start_date,end_date))

    # bucket='customer-aws-ri-sp-recommendation'
    prefix='customer-linkedAccount-RI&SP-recommendation-%s-%s.xlsx' % (start_date,end_date)
    s3_path='s3://{bucket}/{prefix}'.format(bucket = REPORT_BUCKET_NAME, prefix = prefix)
    msg='<!subteam^SJS7FLRUG> & <@U455JGBC7> customer-RI&SP report is ready,Please go to customer AWS Account Download!' #customer slacl channel message
    #msg='<@UFRG38Z2T> customer-RI&SP report is ready!' #zeuikli-test
    send_slack(msg,s3_path)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
