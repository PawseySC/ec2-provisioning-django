import boto3
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to terminate an EC2 instance.This function sits on the AWS Lambda service and is triggered by an API Gateway request.
    """
    try:
        instance_id = event['instance_id']
        logger.info(f"Received request to terminate instance: {instance_id}")
        
        ec2 = boto3.client('ec2')
        
        # Check if instance exists and is not already terminated
        describe_response = ec2.describe_instances(InstanceIds=[instance_id])
        instance_state = describe_response['Reservations'][0]['Instances'][0]['State']['Name']
        logger.info(f"Current instance state: {instance_state}")
        
        # Terminate the instance if it's not already terminated
        if instance_state != 'terminated':
            response = ec2.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminate instance response: {response}")
            return {
                'statusCode': 200,
                'body': f"Successfully initiated termination for instance {instance_id}"
            }
        else:
            logger.info(f"Instance {instance_id} is already terminated")
            return {
                'statusCode': 200,
                'body': f"Instance {instance_id} is already terminated"
            }
        
    except Exception as e:
        logger.error(f"Error terminating instance: {str(e)}", exc_info=True)
        raise