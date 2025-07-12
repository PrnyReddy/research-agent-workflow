# Deployment Guide: Multi-Agent Research Platform on AWS Lambda

## Prerequisites
- AWS account
- AWS CLI configured
- Python 3.10+ runtime
- Required environment variables:
  - ALPHA_VANTAGE_API_KEY
  - NEWS_API_KEY

## Packaging & Deployment

1. **Install dependencies**
   ```
   pip install -r backend/requirements.txt
   ```

2. **Package the Lambda function**
   - Zip the `backend` directory and its dependencies:
     ```
     cd backend
     zip -r lambda_package.zip .
     ```

3. **Create AWS Lambda function**
   - Go to AWS Lambda Console
   - Create a new function (Python 3.10 runtime)
   - Upload `lambda_package.zip` as the deployment package

4. **Set environment variables**
   - In Lambda configuration, add:
     - ALPHA_VANTAGE_API_KEY
     - NEWS_API_KEY

5. **Configure API Gateway (optional)**
   - Create an HTTP API Gateway
   - Connect it to your Lambda function for RESTful access

## Usage

- POST a JSON payload to the API Gateway endpoint:
  ```json
  {
    "task": "Compare the financial outlook and recent news for NVIDIA and AMD."
  }
  ```

- The Lambda function will return agent outputs in a structured JSON response.

## Cloud-Native Principles

- Stateless function: All state is passed in the event payload.
- Modular code: Each tool and agent is a separate module.
- Resilient error handling: All errors are returned as structured JSON.
- Easy integration: Designed for seamless API Gateway and cloud automation.

## Best Practices

- Use AWS Secrets Manager for API keys in production.
- Monitor Lambda logs via CloudWatch.
- Scale via concurrent Lambda invocations.

## Troubleshooting

- Ensure all dependencies are included in the deployment package.
- Check environment variables for correct API keys.
- Review CloudWatch logs for errors.
