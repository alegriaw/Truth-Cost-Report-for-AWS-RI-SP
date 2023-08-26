

import os
import sys
import csv
import boto3
import botocore
import time
from botocore.exceptions import ClientError

def sleep_milliseconds(milliseconds):
    seconds = milliseconds / 1000.0
    time.sleep(seconds)


# init clients
athena = boto3.client('athena')
s3     = boto3.resource('s3')



def retry(func, max_tries=5, *args, **kwargs):
    for i in range(max_tries):
        print(f'retry: {i}, id: {args}')
        try:
           sleep_milliseconds(1000) 
           func(*args, **kwargs)
           print('completed successfully')
           break
        except Exception:
           print(f'Exception: {Exception}')
           continue

# retry(get_athena_data, arg1, arg2, kwarg1="foo", kwarg2="bar")

def poll_status(_id):
    print("1")
    result = athena.get_query_execution( QueryExecutionId = _id )
    print("2")
    state  = result['QueryExecution']['Status']['State']
    print(f"state: {state}")
    if state == 'SUCCEEDED':
        # print(result)
        if result is not None:
            return 'SUCCEEDED'
        else:
            pass
    elif state == 'FAILED':
        print(result)
        raise Exception(state)
    else :
        retry(poll_status,5,_id)


def run_query(query, database, s3_bucket):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': database
        },
        ResultConfiguration={
            'OutputLocation': 's3://'+s3_bucket,
    })

    QueryExecutionId = response['QueryExecutionId']
    result2 = poll_status(QueryExecutionId)
    
    # print(f'poll status result: {result2}')

    print("Query SUCCEEDED: {}".format(QueryExecutionId))

    s3_key = QueryExecutionId + '.csv'
    local_filename = '/tmp/'+QueryExecutionId + '.csv'

    # download result file
    print(f"download result file from:{s3_bucket}")
    try:
        s3.Bucket(s3_bucket).download_file(s3_key, local_filename)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

    # read file to array
    rows = []
    with open(local_filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)

    # delete result file
    if os.path.isfile(local_filename):
        os.remove(local_filename)

    return rows     
