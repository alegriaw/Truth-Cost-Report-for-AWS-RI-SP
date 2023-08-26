import boto3
import json 
from datetime import datetime, timedelta
# from boto3 import botocore
import botocore
from botocore.exceptions import ClientError

client = boto3.client('ce')

# read RecordType List file
# with open('./recordTypeList.json','r') as myfile:
#     data = myfile.read()

# parse file
# recordTypeList = json.loads(data)['list']




def getSavingsPlans():
    client = boto3.client('savingsplans')
    try:
        response = client.describe_savings_plans()

        # print(response)
        return response  
    # except client.exceptions.DataUnavailableException:
    #     return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'DataUnavailableException':
            print("DataUnavailableException")
        return None

# response = getSavingsPlansUtilization('2021-04-01','2021-06-01')
# response = getSavingsPlansUtilizationRecommendation('2021-04-01','2021-06-01')
# print(response)