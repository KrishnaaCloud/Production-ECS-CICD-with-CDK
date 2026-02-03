#!/usr/bin/env python3
import aws_cdk as cdk
from infrastructure.stacks.application_stack import ApplicationCdkStack

app = cdk.App()

ApplicationCdkStack(
    app,
    "UatApplicationStack",
    env={
        "account": "ACCOUNT_ID",
        "region": "ap-south-1"
    }
)

app.synth()
