#!/usr/bin/env python3
"""
Total Life AI - AWS Infrastructure Deployment
Complete production-ready infrastructure using AWS CDK
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elbv2,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_secretsmanager as secrets_manager,
    aws_logs as logs,
    CfnOutput,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class TotalLifeAIStack(Stack):
    """Complete AWS infrastructure for Total Life AI RAG system."""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ========================================
        # NETWORKING - VPC with public/private subnets
        # ========================================
        
        self.vpc = ec2.Vpc(
            self, "TotalLifeAI-VPC",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # ========================================
        # RDS DATABASE - PostgreSQL for production
        # ========================================
        
        # Database security group
        db_security_group = ec2.SecurityGroup(
            self, "Database-SecurityGroup",
            vpc=self.vpc,
            description="Security group for RDS database",
            allow_all_outbound=False
        )
        
        # Database credentials in Secrets Manager
        db_credentials = rds.DatabaseSecret(
            self, "DBCredentials",
            username="totallifeai_admin",
            secret_name="totallifeai/database/credentials"
        )
        
        # RDS PostgreSQL instance
        self.database = rds.DatabaseInstance(
            self, "TotalLifeAI-Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.MICRO  # Start small, can scale up
            ),
            credentials=rds.Credentials.from_secret(db_credentials),
            database_name="totallifeai",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[db_security_group],
            backup_retention=Duration.days(7),
            deletion_protection=False,  # Set to True in production
            auto_minor_version_upgrade=True,
            allocated_storage=20,
            max_allocated_storage=100,  # Auto-scaling storage
            delete_automated_backups=False,
            removal_policy=RemovalPolicy.DESTROY  # For development
        )
        
        # ========================================
        # ECR REPOSITORY - For Docker images
        # ========================================
        
        # Use existing ECR repository
        self.ecr_repository = ecr.Repository.from_repository_name(
            self, "TotalLifeAI-ECR",
            repository_name="totallifeai-backend"
        )
        
        # ========================================
        # ECS CLUSTER - Fargate for scalable containers
        # ========================================
        
        # ECS Cluster
        self.ecs_cluster = ecs.Cluster(
            self, "TotalLifeAI-Cluster",
            vpc=self.vpc,
            cluster_name="totallifeai-cluster",
            container_insights=True
        )
        
        # Task execution role
        task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )
        
        # Task role with permissions for AI services
        task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "AIServicesPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:InvokeModelWithResponseStream",
                                "bedrock:ListFoundationModels"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ssm:GetParameter",
                                "ssm:GetParameters",
                                "ssm:GetParametersByPath"
                            ],
                            resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/totallifeai/*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:DescribeSecret"
                            ],
                            resources=[
                                db_credentials.secret_arn,
                                f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:totallifeai/*"
                            ]
                        )
                    ]
                )
            }
        )
        
        # ========================================
        # APPLICATION LOAD BALANCER
        # ========================================
        
        # ALB security group
        alb_security_group = ec2.SecurityGroup(
            self, "ALB-SecurityGroup",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=False
        )
        
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic"
        )
        
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow HTTPS traffic"
        )
        

        # ========================================
        # ECS FARGATE SERVICE
        # ========================================
        
        # ECS security group
        ecs_security_group = ec2.SecurityGroup(
            self, "ECS-SecurityGroup",
            vpc=self.vpc,
            description="Security group for ECS tasks"
        )
        
        # Allow ALB to reach ECS tasks
        ecs_security_group.add_ingress_rule(
            alb_security_group,
            ec2.Port.tcp(8000),
            "Allow ALB to reach ECS tasks"
        )
        
        # Allow ECS to reach database
        db_security_group.add_ingress_rule(
            ecs_security_group,
            ec2.Port.tcp(5432),
            "Allow ECS to reach PostgreSQL"
        )
        
        # Fargate service with ALB
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "TotalLifeAI-Service",
            cluster=self.ecs_cluster,
            memory_limit_mib=1024,
            cpu=512,
            desired_count=2,  # Start with 2 instances for HA
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(self.ecr_repository, "latest"),
                container_port=8000,
                task_role=task_role,
                execution_role=task_execution_role,
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="totallifeai",
                    log_retention=logs.RetentionDays.ONE_WEEK
                ),
                environment={
                    "ENVIRONMENT": "production",
                    "AWS_DEFAULT_REGION": self.region,
                    "DATABASE_HOST": self.database.instance_endpoint.hostname,
                    "DATABASE_PORT": str(self.database.instance_endpoint.port),
                    "DATABASE_NAME": "totallifeai",
                    "TOGETHER_API_KEY_SSM": "/totallifeai/together-api-key",
                    "OPENAI_API_KEY_SSM": "/totallifeai/openai-api-key",
                    "SECRET_KEY_SSM": "/totallifeai/secret-key"
                },
                secrets={
                    "DATABASE_USERNAME": ecs.Secret.from_secrets_manager(
                        db_credentials, "username"
                    ),
                    "DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
                        db_credentials, "password"
                    ),
                }
            ),
            public_load_balancer=True,
            listener_port=80,
            security_groups=[ecs_security_group],
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )
        )
        
        # Configure health check
        self.fargate_service.target_group.configure_health_check(
            path="/health",
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
            timeout=Duration.seconds(30),
            interval=Duration.seconds(60)
        )
        
        # ========================================
        # AUTO SCALING
        # ========================================
        
        scalable_target = self.fargate_service.service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=10
        )
        
        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2)
        )
        
        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(2)
        )
        
        # ========================================
        # S3 + CLOUDFRONT - Frontend hosting
        # ========================================
        
        # S3 bucket for frontend
        self.frontend_bucket = s3.Bucket(
            self, "Frontend-Bucket",
            bucket_name=f"totallifeai-frontend-{self.account}-{self.region}",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        # CloudFront Origin Access Identity
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment="OAI for Total Life AI frontend"
        )
        
        # Grant CloudFront access to S3 bucket
        self.frontend_bucket.grant_read(origin_access_identity)
        
        # CloudFront distribution
        self.cloudfront_distribution = cloudfront.Distribution(
            self, "Frontend-Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=cloudfront_origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD,
                compress=True
            ),
            additional_behaviors={
                "/api/*": cloudfront.BehaviorOptions(
                    origin=cloudfront_origins.LoadBalancerV2Origin(
                        self.fargate_service.load_balancer,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER
                )
            },
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html"
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html"
                )
            ],
            comment="Total Life AI Frontend Distribution"
        )
        
        
        # ========================================
        # OUTPUTS - Important values for deployment
        # ========================================
        
        CfnOutput(
            self, "DatabaseEndpoint",
            value=self.database.instance_endpoint.hostname,
            description="RDS PostgreSQL endpoint"
        )
        
        CfnOutput(
            self, "DatabasePort",
            value=str(self.database.instance_endpoint.port),
            description="RDS PostgreSQL port"
        )
        
        CfnOutput(
            self, "ECRRepositoryURI",
            value=self.ecr_repository.repository_uri,
            description="ECR repository URI for Docker images"
        )
        
        CfnOutput(
            self, "LoadBalancerDNS",
            value=self.fargate_service.load_balancer.load_balancer_dns_name,
            description="Application Load Balancer DNS name"
        )
        
        CfnOutput(
            self, "CloudFrontDomainName",
            value=self.cloudfront_distribution.distribution_domain_name,
            description="CloudFront distribution domain name"
        )
        
        CfnOutput(
            self, "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            description="S3 bucket name for frontend files"
        )
        
        CfnOutput(
            self, "ClusterName",
            value=self.ecs_cluster.cluster_name,
            description="ECS cluster name"
        )
        
        CfnOutput(
            self, "ServiceName",
            value=self.fargate_service.service.service_name,
            description="ECS service name"
        )


app = cdk.App()

TotalLifeAIStack(
    app, "TotalLifeAI-Prod-Clean",
    description="Complete AWS infrastructure for Total Life AI RAG system"
)

app.synth()
