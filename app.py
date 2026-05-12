#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Environment, Tags

from stangastaden_infra.stacks.mcp_stack import StangastadenMcpStack


def add_tags_to_stack(stack: cdk.Stack, owner: str, team: str) -> None:
    Tags.of(stack).add("Owner", owner)
    Tags.of(stack).add("Team", team)


DEFAULT_ENV = Environment(region="eu-north-1")

app = cdk.App()

mcp_stack = StangastadenMcpStack(
    scope=app,
    construct_id="stangastaden-mcp",
    env=DEFAULT_ENV,
)
add_tags_to_stack(stack=mcp_stack, owner="rayan.bayat01@gmail.com", team="personal")

app.synth()
