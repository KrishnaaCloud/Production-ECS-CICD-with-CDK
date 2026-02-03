from aws_cdk import (
    Stack,
    Tags,
    Duration,
    CfnParameter,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_ecr as ecr,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
)
from constructs import Construct


class ApplicationCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ==================================================
        # STACK TAGS
        # ==================================================
        Tags.of(self).add("Application", "sample-app")
        Tags.of(self).add("Environment", "uat")
        Tags.of(self).add("ManagedBy", "CDK")

        # ==================================================
        # IMAGE TAG PARAMETER (FROM CI)
        # ==================================================
        image_tag = CfnParameter(
            self,
            "ImageTag",
            type="String",
            description="Docker image tag to deploy (e.g. build number)"
        )

        # ==================================================
        # EXISTING VPC
        # ==================================================
        vpc = ec2.Vpc.from_lookup(
            self,
            "ExistingVpc",
            vpc_id="vpc-xxxxxxxxxxxxxxxxx"
        )

        # ==================================================
        # SECURITY GROUPS
        # ==================================================
        ecs_sg = ec2.SecurityGroup.from_security_group_id(
            self,
            "EcsSecurityGroup",
            security_group_id="sg-xxxxxxxxxxxxxxxxx"
        )

        alb_sg = ec2.SecurityGroup.from_security_group_id(
            self,
            "AlbSecurityGroup",
            security_group_id="sg-yyyyyyyyyyyyyyyyy"
        )

        # ==================================================
        # ECS CLUSTER
        # ==================================================
        cluster = ecs.Cluster(
            self,
            "ApplicationCluster",
            cluster_name="uat-application-cluster",
            vpc=vpc
        )

        # ==================================================
        # AUTO SCALING GROUP (EC2 CAPACITY)
        # ==================================================
        asg = autoscaling.AutoScalingGroup(
            self,
            "ApplicationAsg",
            vpc=vpc,
            instance_type=ec2.InstanceType("t3a.medium"),
            machine_image=ec2.MachineImage.generic_linux(
                {"ap-south-1": "ami-xxxxxxxxxxxxxxxxx"}
            ),
            min_capacity=1,
            max_capacity=1,
            desired_capacity=1,
            security_group=ecs_sg,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            require_imdsv2=True
        )

        capacity_provider = ecs.AsgCapacityProvider(
            self,
            "ApplicationCapacityProvider",
            auto_scaling_group=asg
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        # ==================================================
        # ECR REPOSITORY
        # ==================================================
        ecr_repo = ecr.Repository.from_repository_name(
            self,
            "ApplicationEcrRepo",
            "sample-api"
        )

        # ==================================================
        # LOG GROUP
        # ==================================================
        log_group = logs.LogGroup.from_log_group_name(
            self,
            "ApplicationLogGroup",
            log_group_name="/ecs/sample-api"
        )

        # ==================================================
        # TASK DEFINITION
        # ==================================================
        task_def = ecs.Ec2TaskDefinition(
            self,
            "ApplicationTaskDefinition",
            family="sample-api",
            network_mode=ecs.NetworkMode.AWS_VPC
        )

        container = task_def.add_container(
            "ApplicationContainer",
            container_name="sample-api",
            image=ecs.ContainerImage.from_ecr_repository(
                ecr_repo,
                tag=image_tag.value_as_string   # 👈 VERSIONED IMAGE
            ),
            memory_reservation_mib=512,
            logging=ecs.AwsLogDriver(
                log_group=log_group,
                stream_prefix="ecs"
            )
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=8000)
        )

        # ==================================================
        # ECS SERVICE (WITH CIRCUIT BREAKER)
        # ==================================================
        service = ecs.Ec2Service(
            self,
            "ApplicationService",
            service_name="sample-api-service",
            cluster=cluster,
            task_definition=task_def,
            desired_count=1,
            security_groups=[ecs_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider=capacity_provider.capacity_provider_name,
                    weight=1
                )
            ],
            deployment_controller=ecs.DeploymentController(
                type=ecs.DeploymentControllerType.ECS
            ),
            circuit_breaker=ecs.DeploymentCircuitBreaker(
                rollback=True
            ),
            propagate_tags=ecs.PropagatedTagSource.SERVICE
        )

        # ==================================================
        # APPLICATION LOAD BALANCER
        # ==================================================
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "ApplicationAlb",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name="uat-application-alb",
            security_group=alb_sg
        )

        # ==================================================
        # TARGET GROUP
        # ==================================================
        target_group = elbv2.ApplicationTargetGroup(
            self,
            "ApplicationTargetGroup",
            vpc=vpc,
            port=8000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                healthy_http_codes="200",
                interval=Duration.seconds(30)
            )
        )

        target_group.add_target(service)

        # ==================================================
        # CERTIFICATE
        # ==================================================
        certificate = acm.Certificate.from_certificate_arn(
            self,
            "ApplicationCertificate",
            "arn:aws:acm:region:account-id:certificate/xxxxxxxxxxxxxxxx"
        )

        # ==================================================
        # LISTENERS
        # ==================================================
        alb.add_listener(
            "HttpListener",
            port=80,
            open=True,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443"
            )
        )

        https_listener = alb.add_listener(
            "HttpsListener",
            port=443,
            certificates=[certificate],
            open=True,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="text/plain",
                message_body="Not Found"
            )
        )

        https_listener.add_action(
            "HostRoutingRule",
            priority=10,
            conditions=[
                elbv2.ListenerCondition.host_headers(
                    ["api.example.com"]
                )
            ],
            action=elbv2.ListenerAction.forward([target_group])
        )
