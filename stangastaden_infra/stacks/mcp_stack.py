from pathlib import Path

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class StangastadenMcpStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        project_root = Path(__file__).resolve().parents[2]

        fn = _lambda.DockerImageFunction(
            self,
            "Function",
            code=_lambda.DockerImageCode.from_image_asset(str(project_root)),
            memory_size=1024,
            timeout=Duration.seconds(60),
            architecture=_lambda.Architecture.X86_64,
        )

        api = apigw.LambdaRestApi(
            self,
            "Api",
            handler=fn,
            proxy=True,
            description="Stangastaden MCP API",
        )

        CfnOutput(
            self,
            "ApiUrl",
            value=api.url,
            description="API Gateway base URL",
        )
        CfnOutput(
            self,
            "McpUrl",
            value=f"{api.url}mcp",
            description="Paste into Claude: Settings -> Connectors -> Add custom connector",
        )
