import boto3
import json 
from datetime import datetime, timedelta
# from boto3 import botocore
import botocore

client = boto3.client('ce')


def getSavingsPlansUtilization(start_date,end_date):
    client = boto3.client('ce')
    try:
        response = client.get_savings_plans_utilization(
            TimePeriod={
                'Start':start_date,
                'End':end_date
            }
            # Granularity='MONTHLY',
            # Metrics=[
            #     'UnblendedCost',
            # ],
            # GroupBy=[
            #     {
            #         'Type': 'DIMENSION',
            #         'Key': 'LINKED_ACCOUNT'
            #     },
            # ]
        )

        # print(response)
        return response  
    except client.exceptions.DataUnavailableException:
        return None

def getSavingsPlansUtilizationRecommendation():
    client = boto3.client('ce')

    response = client.get_savings_plans_purchase_recommendation(
        SavingsPlansType='COMPUTE_SP',
        TermInYears='ONE_YEAR',
        PaymentOption='ALL_UPFRONT',
        AccountScope='LINKED',
        LookbackPeriodInDays='SIXTY_DAYS'
        
    )

    # print(response)
    return response  


def getSavingsPlansEC2UtilizationRecommendation():
    client = boto3.client('ce')

    response = client.get_savings_plans_purchase_recommendation(
        SavingsPlansType='EC2_INSTANCE_SP',
        TermInYears='ONE_YEAR',
        PaymentOption='ALL_UPFRONT',
        AccountScope='LINKED',
        LookbackPeriodInDays='SIXTY_DAYS'
        
    )

    # print(response)
    return response  


def getReservationPurchaseRecommendation(service):
    client = boto3.client('ce')

    response = client.get_reservation_purchase_recommendation(
        # AccountId='string',
        Service=service,
        # Filter={
        #     'Or': [
        #         {'... recursive ...'},
        #     ],
        #     'And': [
        #         {'... recursive ...'},
        #     ],
        #     'Not': {'... recursive ...'},
        #     'Dimensions': {
        #         'Key': 'AZ'|'INSTANCE_TYPE'|'LINKED_ACCOUNT'|'LINKED_ACCOUNT_NAME'|'OPERATION'|'PURCHASE_TYPE'|'REGION'|'SERVICE'|'SERVICE_CODE'|'USAGE_TYPE'|'USAGE_TYPE_GROUP'|'RECORD_TYPE'|'OPERATING_SYSTEM'|'TENANCY'|'SCOPE'|'PLATFORM'|'SUBSCRIPTION_ID'|'LEGAL_ENTITY_NAME'|'DEPLOYMENT_OPTION'|'DATABASE_ENGINE'|'CACHE_ENGINE'|'INSTANCE_TYPE_FAMILY'|'BILLING_ENTITY'|'RESERVATION_ID'|'RESOURCE_ID'|'RIGHTSIZING_TYPE'|'SAVINGS_PLANS_TYPE'|'SAVINGS_PLAN_ARN'|'PAYMENT_OPTION'|'AGREEMENT_END_DATE_TIME_AFTER'|'AGREEMENT_END_DATE_TIME_BEFORE',
        #         'Values': [
        #             'string',
        #         ],
        #         'MatchOptions': [
        #             'EQUALS'|'ABSENT'|'STARTS_WITH'|'ENDS_WITH'|'CONTAINS'|'CASE_SENSITIVE'|'CASE_INSENSITIVE',
        #         ]
        #     },
        #     'Tags': {
        #         'Key': 'string',
        #         'Values': [
        #             'string',
        #         ],
        #         'MatchOptions': [
        #             'EQUALS'|'ABSENT'|'STARTS_WITH'|'ENDS_WITH'|'CONTAINS'|'CASE_SENSITIVE'|'CASE_INSENSITIVE',
        #         ]
        #     },
        #     'CostCategories': {
        #         'Key': 'string',
        #         'Values': [
        #             'string',
        #         ],
        #         'MatchOptions': [
        #             'EQUALS'|'ABSENT'|'STARTS_WITH'|'ENDS_WITH'|'CONTAINS'|'CASE_SENSITIVE'|'CASE_INSENSITIVE',
        #         ]
        #     }
        # },
        AccountScope='LINKED',
        LookbackPeriodInDays='SIXTY_DAYS',
        TermInYears='ONE_YEAR',
        PaymentOption='ALL_UPFRONT',
        # ServiceSpecification={
        #     'EC2Specification': {
        #         'OfferingClass': 'STANDARD'|'CONVERTIBLE'
        #     }
        # },
        # PageSize=123,
        # NextPageToken='string'
        
    )

    # print(response)
    return response  

def getRIUtilizationByLinkedAccount(start_date,end_date,service_type,linkedaccount):
    client = boto3.client('ce')
    response = client.get_reservation_utilization(
        TimePeriod={
            'Start':start_date,
            'End':end_date
        },
        # GroupBy=[
        #     {
        #         'Type': 'DIMENSION',
        #         'Key': 'LINKED_ACCOUNT'
        #     },
        # ],
        Granularity='MONTHLY',
        Filter={
            "And": [
                {'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': [
                            linkedaccount,
                        ]
                    },
                },
                {'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [
                            service_type,
                        ]
                    },
                }    
            ]
        },
        # NextPageToken='string'
    )
    print(response)
    return response


def getRIUtilizationGroupBySubscriptionId(start_date,end_date,service_type):
    client = boto3.client('ce')
    response = client.get_reservation_utilization(
        TimePeriod={
            'Start':start_date,
            'End':end_date
        },
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SUBSCRIPTION_ID'
            },
        ],
        # Granularity='MONTHLY',
        Filter={
            'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [
                        service_type,
                    ]
                }
        },
        # NextPageToken='string'
    )
    print(response)
    return response


def getRICoverageByLinkedAccount(start_date,end_date,service_type,linkedaccount):
    client = boto3.client('ce')
    response = client.get_reservation_coverage(
        TimePeriod={
            'Start':start_date,
            'End':end_date
        },
        GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'INSTANCE_TYPE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
        ],
        # Granularity='MONTHLY',
        Filter={
            "And": [
                {'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': linkedaccount
                    },
                },
                {'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [
                            service_type,
                        ]
                    },
                }
                
            ]
        },
        # NextPageToken='string'
    )
    print(response)
    return response
    

def getSPUtilizationByLinkedAccount(start_date,end_date,linkedaccount):
    client = boto3.client('ce')
    response = client.get_savings_plans_utilization(
        TimePeriod={
            'Start':start_date,
            'End':end_date
        },
        # GroupBy=[
        #     {
        #         'Type': 'DIMENSION',
        #         'Key': 'LINKED_ACCOUNT'
        #     },
        # ],
        Granularity='MONTHLY',
        Filter={
            'Dimensions': {
                'Key': 'LINKED_ACCOUNT',
                'Values': [
                    linkedaccount,
                ]
            },
        },
        # NextPageToken='string'
    )
    print(response)
    return response

# response = getSavingsPlansUtilization('2021-04-01','2021-06-01')
# response = getSavingsPlansUtilizationRecommendation('2021-04-01','2021-06-01')
# print(response)