<p align="center">
  <a href="" rel="noopener">
 <!--img width=200px height=200px src="https://i.imgur.com/6wj0hh6.jpg" alt="Project logo"--></a>
</p>

<h3 align="center">Truth Cost Report for AWS Reserved Instance(RI) and Savings Plan (SP) recommandation</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/kylelobo/The-Documentation-Compendium.svg)](https://github.com/alegriaw/Truth-Cost-Report-for-AWS-RI-SP/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/alegriaw/Truth-Cost-Report-for-AWS-RI-SP/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> <!-- some title description here-->
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Running the tests](#tests)
- [Built & Testing](#built_testing)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

This sample code is for customer to run lambda functions on their envorinment to genereate RI/SP recommedatoin reports for their linked accounts as execl files.

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your AWS Account environment for development and testing purposes. 
</br>See [Built & Testing](#built_testing) for notes on how to deploy the project on your AWS account.

### Prerequisites

[1] **In the Billing Console under your AWS account, add a Cost & Usage report with *Amazon Athena* enabled.**

![CUR](https://github.com/alegriaw/truth-cost-report-RI-SP/assets/10775909/22904108-de58-4c12-b9c7-4c03dec52cd3)

[2] **Setting up Athena query table with CloudFormation**
* https://docs.aws.amazon.com/cur/latest/userguide/use-athena-cf.html </br>
`Wait for the first report to be delivered to your Amazon S3 bucket. It can take up to 24 hours for AWS to deliver your first report.`

![yml](https://github.com/alegriaw/truth-cost-report-RI-SP/assets/10775909/3da1914e-6c72-4786-a9c8-c70623d9f6d5)

[3] **In the *same region* of Athen and S3, open CloudFormation, create a new stack to execute the .yml file, and generate a CUR query table in Athena.** 

![cfn_stack](https://github.com/alegriaw/truth-cost-report-RI-SP/assets/10775909/dfaad9c7-763d-4a36-968c-6cb4d8200f88)

[4] **After successfully generating a CUR table in Athena, you will need to set the S3 Bucket location where the Athena Query Result will be stored. Please go to the Athena `Settings` tab, and fill in the S3 bucket location where you want to store the Athena `query result`. Once the settings are complete, you can try running a query to see if the setup was successful.** 

![athena query result](https://github.com/alegriaw/truth-cost-report-RI-SP/assets/10775909/230b5368-07ab-4de4-baab-5526d738c3a2)


(we set a new S3 bucket `aws-cur-athena-query-results-us-east-1` here.)

[5] Create a new S3 bucket: `customer-aws-ri-sp-recommendation` as your output report destination bucket.

### Installing 

A step by step series of examples that tell you how to get a development env running.

[1] **Create a folder in your local environment to store files related to Lambda functions. Then, create a virtual environment in that folder and install the xlsxwriter package.** 

(You can also download the github source code with xlsxwriter folder instead of `pip install xlsxwriter` )

```shell
mkdir lambda_function
cd lambda_function
python3 -m venv venv
source venv/bin/activate
pip install xlsxwriter
```

[2] **Compress all downloaded source code and packages into one zip file.**

```shell
zip -r deployment_package.zip *
```

[3] **In the AWS Management Console, navigate to the Lambda service and create a new Lambda function with the `deployment_package.zip` file.** 

Choose your preferred runtime, such as Python 3.11.


## 🔧 Running the tests <a name = "tests"></a>

### 1. Set IAM policy:

- Go to `Configuration` > `Permissions` and find the Execution role. Click the link to open the IAM role settings.

- Reference the _IAM_Policy.json_ file to config your lambda execution IAM Role policy and add `AWSGlueConsoleFullAccess` permission policy for this program running.

_(Optional)_  if you want to export your lambda log to CloudWatch Logs, add `CloudWatchLogFullAccess` permission policy

![IAM policy](https://github.com/alegriaw/truth-cost-report-RI-SP/assets/10775909/e6ff87c9-1ff2-4597-a638-455d1a52e373)

### 2. Parameter Setup and Modification in Source Code

In the `lambda_function.py` file, based on the previous steps, input the previously set configuration values

```python
# configuration for s3
REPORT_BUCKET_NAME = "customer-aws-ri-sp-recommendation" # output report destination s3 bucket
PARAMETER_PATH = "customer-account-list.csv" # your report account list in report s3 bucket
# configuration for Athena
ATHENA_QUERY_RESULT_S3_BUCKET = 'aws-cur-athena-query-results-us-east-1'  # Query result s3 bucket @ N. virginia
CUR_DATABASE_NAME  = 'athenacurcfn_cur_report'  
CUR_TABLE_NAME = 'cur_report' 

DELTA_DAYS = 60
```

- Create a new file called `customer-account-list.csv`(you can download the sample file from github) and input the AWS Account ID and Name for generating recommendations. Put this file in the S3 bucket `customer-aws-ri-sp-recommendation` which created in the Prerequisites[5] steps.


## ⛏️ Built & Testing <a name = "built_testing"></a>

Create a test for your lambda function, and then run and check the generated report under the S3 bucket `customer-aws-ri-sp-recommendation`.


## ✍️ Authors <a name = "authors"></a>

- [@JillWang](https://github.com/alegriaw) - Idea & Initial work & Update
- [@JayHuang]() - Contributor & Initial work

<!--See also the list of [contributors](https://github.com/kylelobo/The-Documentation-Compendium/contributors) who participated in this project.-->

## 🎉 Acknowledgements <a name = "acknowledgement"></a>

- Hat tip to anyone whose code was used
- Inspiration
- References
