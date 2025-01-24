# Import third party packages.
from aws_cdk import (
    App,
    aws_batch as batch,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    Environment,
    Stack
)

class CloudformationStack(Stack):

    def __init__(self, app: App, id: str, **kwargs) -> None:
        super().__init__(app, id, **kwargs)

        # Create a VPC to run the EC2 instances in
        vpc = ec2.Vpc(
            scope=self, 
            id='Vpc'
        )

        # Make an ECR repo to store the docker images we will use to run code
        ecr_repo = ecr.Repository(
            scope=self,
            id=f'EcrRepo',
            repository_name='my_ecr_repo'
        )

        # Allow read and write access to S3 objects
        s3_bucket_statement = iam.PolicyStatement(
            actions=[
                's3:GetObject',
                's3:PutObject'
            ],
            effect=iam.Effect.ALLOW
        )

        # Specify the bucket to provision read/write to using the ARN
        s3_bucket_statement.add_resources('arn:aws:s3:::my-s3-bucket/*')

        # Allow us to access a secret from secrets manager
        secret_statement = iam.PolicyStatement(
            actions=[
                'secretsmanager:GetSecretValue'
                ],
            effect=iam.Effect.ALLOW
        )

        # Specify the secret using the ARN
        secret_statement.add_resources('arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret-GH69Bf4')

        # Create an IAM role for the EC2 instances
        instance_role = iam.Role(
            scope=self,
            id=f'InstanceRole',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonEC2ContainerServiceforEC2Role')
            ]
        )

        # Add the policies to the instance role
        instance_role.add_to_policy(s3_bucket_statement)
        instance_role.add_to_policy(secret_statement)

        # Create a service role for batch
        iam.Role(
            scope=self,
            id=f'ServiceRole',
            assumed_by=iam.ServicePrincipal('batch.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSBatchServiceRole')
            ]
        )

        # Create the instance profile for batch
        instance_profile = iam.CfnInstanceProfile(
            scope=self,
            id=f'InstanceProfile',
            roles=[instance_role.role_name]
        )

        # Create a security group the gives the batch instances outbound traffic only
        security_group = ec2.SecurityGroup(
            scope=self,
            id=f'SecurityGroup',
            vpc=vpc,
            allow_all_outbound=True
        )

        # Create a block device for data storage on the instances
        block_device = ec2.BlockDevice(
            device_name='/dev/xvda',
            volume=ec2.BlockDeviceVolume.ebs(50)
        )

        # Create a launch template for our storage
        launch_template = ec2.LaunchTemplate(
            scope=self,
            id=f'LaunchTemplate',
            block_devices=[block_device],
            launch_template_name=f'my-launch-template'
        )

        # Define the compute environment for batch.

        # Because the AWS CDK does not currently have a stable compute environment construct, we use a Cfn construct that
        # maps 1 to 1 with the cloudformation template used to create a batch compute environment.

        # CDK Cfn Construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_batch/CfnComputeEnvironment.html
        # Batch Compute Environment Cloudformation Template: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-batch-computeenvironment.html
        compute_environment = batch.CfnComputeEnvironment(
            scope=self,
            id=f'ComputeEnvironment',
            type='MANAGED',
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                maxv_cpus=2,
                subnets=[x.subnet_id for x in vpc.private_subnets],
                type='EC2',
                allocation_strategy='BEST_FIT_PROGRESSIVE',
                ec2_configuration=[
                    batch.CfnComputeEnvironment.Ec2ConfigurationObjectProperty(
                        image_type='ECS_AL2'
                        )
                    ],
                instance_role=instance_profile.attr_arn,
                instance_types=['m5.xlarge', 'm5.2xlarge', 'm5.4xlarge'],
                launch_template=batch.CfnComputeEnvironment.LaunchTemplateSpecificationProperty(
                    launch_template_id=launch_template.launch_template_id,
                    launch_template_name=launch_template.launch_template_name,
                    version='$Latest'
                ),
                security_group_ids=[security_group.security_group_id]
                )
            )

        # Define the job queue where batch will schedule runs

        # Because the AWS CDK does not currently have a stable batch job queue construct, we use a Cfn construct that
        # maps 1 to 1 with the cloudformation template used to create a batch compute environment.

        # CDK Cfn Construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_batch/CfnJobQueue.html
        # Batch Job Queue Cloudformation Template: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-batch-jobqueue.html
        batch.CfnJobQueue(
            scope=self,
            id=f'JobQueue',
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    compute_environment=compute_environment.ref,
                    order=1
                    )
                ],
            priority=1
            )

        # Define the job definition for batch

        # Because the AWS CDK does not currently have a stable batch job definition construct, we use a Cfn construct that
        # maps 1 to 1 with the cloudformation template used to create a batch compute environment.

        # CDK Cfn Construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_batch/CfnJobDefinition.html
        # Batch Job Definition Cloudformation Template: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-batch-jobdefinition.html
        batch.CfnJobDefinition(
            scope=self,
            id=f'JobDefinition',
            type='container',
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                    image=f'{self.account}.dkr.ecr.{self.region}.amazonaws.com/{ecr_repo.repository_name}:hello-world-image',
                    command=['python', 'hello_world.py'],
                    resource_requirements=[
                        batch.CfnJobDefinition.ResourceRequirementProperty(
                            type='VCPU',
                            value='4'
                        ),
                        batch.CfnJobDefinition.ResourceRequirementProperty(
                            type='MEMORY',
                            value='8192'
                        )
                    ]
                )
            )

app = App()

# Setup the environment
stack_environment = Environment(
    account='123456789012',
    region='us-west-1'
)

# Create the stack of resources.
CloudformationStack(
    app=app,
    id=f'CloudformationStack',
    env=stack_environment
    )

# Synthesize our CloudFormation stack.
app.synth()
