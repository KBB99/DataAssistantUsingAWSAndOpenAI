import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

// Gets Pinpoint and OpenAI API keys from environment variables
const pinpoint_application_id = process.env.PINPOINT_APPLICATION_ID;
const openai_api_key = process.env.OPENAI_API_KEY;

export class OpenAIPlusAWSStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Defines an on-demand DynamoDB Table to index conversation index with the phone number
    const conversationIndexTable = new dynamodb.Table(this, 'ConversationIndexTable', {
      partitionKey: { name: 'phone_number', type: dynamodb.AttributeType.STRING },
      tableName: 'ConversationIndexTable',
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // Defines a DynamoDB Table to store conversation
    const conversationTable = new dynamodb.Table(this, 'ConversationTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      tableName: 'ConversationTable',
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // Defines a DynamoDB Table to store extracted data
    const extractedDataTable = new dynamodb.Table(this, 'ExtractedDataTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      tableName: 'ExtractedDataTable',
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // Defines an Python Lambda resource AIMessageProcessor
    const AIMessageProcessor = new lambda.Function(this, 'AIMessageProcessor', {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset('lambda'),
      handler: 'AIMessageProcessor.lambda_handler',
      timeout: cdk.Duration.seconds(60),
    });

    // Add requests lambda layer to AIMessageProcessor
    const requestsLayer = lambda.LayerVersion.fromLayerVersionArn(this, 'requestsLayer', 'arn:aws:lambda:us-east-1:377190169022:layer:requests:2');
    AIMessageProcessor.addLayers(requestsLayer);

    // Grant Lambda function access to DynamoDB tables
    conversationIndexTable.grantReadWriteData(AIMessageProcessor);
    conversationTable.grantReadWriteData(AIMessageProcessor);
    extractedDataTable.grantReadWriteData(AIMessageProcessor);

    // API Gateway Lambda Rest API 'AIChatProcessor'
    const api = new apigateway.LambdaRestApi(this, 'AIChatProcessor', {
      handler: AIMessageProcessor
    });

    // Grant Lambda function role access to send messages through pinpoint
    const pinpointPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['mobiletargeting:SendMessages'],
      resources: ['*']
    });

    AIMessageProcessor.addToRolePolicy(pinpointPolicy);

    // Stores OpenAI API key in AWS SSM Parameter Store
    const openAIKey = new ssm.StringParameter(this, 'OpenAIKey', {
      description: 'OpenAI API Key',
      parameterName: 'OpenAIKey',
      stringValue: openai_api_key!,
    });

    // Grant Lambda function role access to read OpenAI API key from SSM Parameter Store
    const ssmPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['ssm:GetParameter'],
      resources: [openAIKey.parameterArn]
    });

    AIMessageProcessor.addToRolePolicy(ssmPolicy);

    // Pass SSM parameter name to Lambda function
    AIMessageProcessor.addEnvironment('OPENAI_API_KEY_SSM_PARAMETER_NAME', 'OpenAIKey');

    // Pass DynamoDB table names to Lambda function
    AIMessageProcessor.addEnvironment('CONVERSATION_INDEX_TABLE_NAME', conversationIndexTable.tableName);
    AIMessageProcessor.addEnvironment('CONVERSATION_TABLE_NAME', conversationTable.tableName);
    AIMessageProcessor.addEnvironment('EXTRACTED_DATA_TABLE_NAME', extractedDataTable.tableName);

    // Pass pinpoint application id to Lambda function
    AIMessageProcessor.addEnvironment('PINPOINT_APPLICATION_ID', pinpoint_application_id!);
  }
}
