import json

THRESHOLD = .85

def lambda_handler(event, context):

    # Grab the inferences from the event
    inferences = event['body']['inferences']
    inferences = [float(value) for value in inferences[1:-1].split(',')]

    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = max(inferences) >= THRESHOLD

    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        "statusCode": 200,
        "body": {
            "image_data": event['body']['image_data'],
            "s3_bucket": event['body']['s3_bucket'],
            "s3_key": event['body']['s3_key'],
            "inferences": event['body']['inferences'],
        }
    }