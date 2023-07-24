import * as cdk from "aws-cdk-lib";
import { Duration } from "aws-cdk-lib";
import { Cors, LambdaIntegration, RestApi } from "aws-cdk-lib/aws-apigateway";
import { AttributeType, Table } from "aws-cdk-lib/aws-dynamodb";
import { Code, Function, Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import path = require("path");

const OPEN_API_KEY = process.env.OPEN_API_KEY;
const DAILY_TOKEN_THRESHOLD = "1000000";
const MODEL = "gpt-3.5-turbo";

export class ThrottledMlApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const tokenTable = new Table(this, "OpenAITokenConsumption", {
      partitionKey: { name: "date", type: AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const handler = new Function(this, "OpenAIHandler", {
      runtime: Runtime.PYTHON_3_10,
      code: Code.fromAsset(path.join(__dirname, "../resources/lambda_src/throttled_open_ai"), {
        bundling: {
          image: Runtime.PYTHON_3_10.bundlingImage,
          command: [
            "bash",
            "-c",
            [
              "pip install -r requirements.txt -t /asset-output",
              "echo 'COMPLETED INSTALL'",
              "cp -ru . /asset-output"
            ].join("&& ")
          ],
        },
      }),
      handler: "index.handler",
      environment: {
        TOKEN_TABLE_NAME: tokenTable.tableName,
        OPEN_API_KEY: OPEN_API_KEY || '',
        DAILY_TOKEN_THRESHOLD,
        MODEL
      },
      timeout: Duration.minutes(10),
      memorySize: 1024,
    });

    tokenTable.grantReadWriteData(handler);

    const api = new RestApi(this, "ThrottledOpenAI", {
      restApiName: "ThrottledOpenAI",
      deployOptions: {
        throttlingRateLimit: 1,
        throttlingBurstLimit: 2,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: Cors.ALL_ORIGINS,
        allowHeaders: ['*']
      }
    });

    const integration = new LambdaIntegration(handler);
    api.root.addMethod("POST", integration);
  }
}
