#OpenAIAndAWSDataAssistant

To get the project up and running, you need to have the following installed:

CDK
AWS CLI
NodeJS
Python 3.6

Once you have the above installed, you can run the following commands to get the back-end up and running:

```bash
cd backend
npm i
npx cdk deploy
```

Save the API Gateway URL that is outputted by the above command. You will need it to run the front-end.

Once the backend is deployed, you can run the following commands to get the front-end up and running:

```bash
echo "API_GATEWAY_URL=<your-api-gateway-url>" > .env.local
cd frontend
npm i
npm run dev
```
