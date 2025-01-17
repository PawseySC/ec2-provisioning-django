import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to stop an EC2 instance. This function sits on the AWS Lambda service and is triggered by an API Gateway request.
    """
    try:
        instance_id = event['instance_id']
        logger.info(f"Received request to stop instance: {instance_id}")
        
        ec2 = boto3.client('ec2')
        
        # Check if instance exists and is running
        describe_response = ec2.describe_instances(InstanceIds=[instance_id])
        instance_state = describe_response['Reservations'][0]['Instances'][0]['State']['Name']
        logger.info(f"Current instance state: {instance_state}")
        
        # Stop the instance if it's running
        if instance_state == 'running':
            response = ec2.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Stop instance response: {response}")
            return {
                'statusCode': 200,
                'body': f"Successfully initiated shutdown for instance {instance_id}"
            }
        else:
            logger.info(f"Instance {instance_id} is not running (current state: {instance_state})")
            return {
                'statusCode': 200,
                'body': f"Instance {instance_id} is already in state: {instance_state}"
            }
        
    except Exception as e:
        logger.error(f"Error stopping instance: {str(e)}", exc_info=True)
        raise
