# aws-batch-simple

## Purpose
AWS Batch is a service provided by AWS to run batch compute jobs. Oftentimes, it can be used in place of AWS lambda when constraints native to lambda are a concern (the 15 minute runtime timeout, for example). Some common use cases for AWS Batch include:
- Training ML Models
- Custom ETL jobs
- Data intensive research jobs

This repository contains an example of defining the infrastructure necessary for running a single docker container (using the AWS CDK) and deploying that infrastructure using Github actions. I was unable to find an example of this specific use case online, so I made one. This is only an example. To use the code, users must replace parameters (like account IDs, resources names, etc.) with their own unique values

## Repository Contents
- **cdk_app/** -> Contains all code for using the AWS CDK to generate infrastructure
    - **app.py** -> Contains an example stack defined in python with some configurations as well (egress only security groups, IAM permissions for reading secrets, etc.)
    - **cdk.json** -> The configuration file for running the CDK
    - **requirements.txt** -> The text file containing the python packages for the CDK app
- **docker/** -> Contains all the files for deploying a simple "hello world" python script in a docker container
    - **Dockerfile** -> The dockerfile for the container
    - **hello_world.py** -> A simple "hello world" python application
    - **requirements.txt** -> The text file containing the python packages we need to run our docker container, with examples for a machine learning use case
- **.github/workflows/** -> Contains configuration files for a Github Actions pipeline
    - **github_actions_pipeline.yaml** -> An example pipeline for deploying our resource stack using the AWS CDK

## Key Difficulties and Considerations
The AWS CDK does not provide stable, high level constructs for AWS Batch resources. In order to leverage the CDK to create the infrastructure for batch jobs, you need to use the lower level Cfn templates. These templates map one-to-one with cloudformation templates, but are less intuitive to implement. This repository contains some examples demonstrating how to use the low level Cfn templates with links to the relevant documentation in the code.

For those attempting to use large language models to write CDK code, they cannot reliably write the code for AWS Batch. They work well for defining common AWS resources with higher level constructs in the CDK (S3, IAM permissions, VPCs, etc.) but are not reliable for less mature resources. They will often hallucinate and write sudo-code defining infrastructure for batch that does not work. Users need to roll up their sleeves and write the CDK code the old fashioned way.

For those concerned with cost, it is best to leverage spot instances in AWS Batch. If availability of instances is a concern, one can use on-demand instances and specify the specific instance type they want to use. It is crucial to ensure the parameters for the job definition are within the computing resources of the underlying EC2 instance, otherwise the jobs will not run. The underlying instance requires some compute and memory for other tasks besides running the docker container. It is recommended to specify parameters (specifically memory) slightly less than the underlying instance. For example, if you want to use an m5.xlarge, specify 15000 bytes of memory in your job definition. This falls slightly below the 16384 bytes available to the m5.xlarge instance.

## Deploying the Docker Container
The following commands can be run inside the **docker/** directory to compile and push the docker container to an AWS ECR repository. Strings that fall between the < > characters should be replaced with actual values. For example, <aws-region> could be replaced with "us-west-1".

1. ```aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com```
2. ```docker build -t <image-name> .```
3. ```docker tag <image-name>:latest <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/<ecr-repo-name>:latest```
4. ```docker push <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/<ecr-repo-name>:latest```

## AWS Cloud Development Kit
- [AWS CDK](https://docs.aws.amazon.com/cdk/)
- [AWS CDK Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [AWS CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/)
- [AWS Batch](https://aws.amazon.com/batch/)
- [AWS Cloudformation - Batch Docs](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_Batch.html)
