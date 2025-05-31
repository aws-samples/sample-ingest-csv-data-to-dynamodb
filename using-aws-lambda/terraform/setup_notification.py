import json
import boto3
import urllib3

def handler(event, context):
    """
    Custom resource handler for setting up S3 bucket notifications.
    This is a simplified version that works with Terraform's aws_s3_bucket_notification resource.
    """
    try:
        print("Received event: " + json.dumps(event))
        
        # This function is kept for compatibility but Terraform handles the notification
        # configuration directly through aws_s3_bucket_notification resource
        
        response_data = {
            'Status': 'SUCCESS',
            'Reason': 'S3 notification configured by Terraform',
            'PhysicalResourceId': 'custom-s3-notification-setup',
            'Data': {}
        }
        
        send_response(event, context, response_data)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        response_data = {
            'Status': 'FAILED',
            'Reason': str(e),
            'PhysicalResourceId': 'custom-s3-notification-setup',
            'Data': {}
        }
        send_response(event, context, response_data)

def send_response(event, context, response_data):
    """
    Send response to CloudFormation custom resource endpoint
    """
    response_url = event.get('ResponseURL')
    if not response_url:
        print("No ResponseURL found, skipping response")
        return
        
    response_body = json.dumps({
        'Status': response_data['Status'],
        'Reason': response_data['Reason'],
        'PhysicalResourceId': response_data['PhysicalResourceId'],
        'StackId': event.get('StackId', ''),
        'RequestId': event.get('RequestId', ''),
        'LogicalResourceId': event.get('LogicalResourceId', ''),
        'Data': response_data['Data']
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(response_body))
    }
    
    try:
        http = urllib3.PoolManager()
        response = http.request(
            'PUT',
            response_url,
            body=response_body,
            headers=headers
        )
        print(f"Response sent successfully: {response.status}")
    except Exception as e:
        print(f"Error sending response: {str(e)}")

