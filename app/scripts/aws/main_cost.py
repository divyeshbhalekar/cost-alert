import boto3
import re
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from dotenv import load_dotenv
# Load environment variables from .env
def run_aws_cost_main():
    load_dotenv()


    # Specify your AWS credentials
    aws_access_key_id = aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')  # Default region if not specified

    # Check if credentials are set
    if aws_access_key_id is None or aws_secret_access_key is None:
        raise ValueError("AWS credentials not set in environment variables.")

    # Specify your Slack API token and channel
    slack_token = os.environ.get('SLACK_TOKEN')
    slack_channel = os.environ.get('SLACK_CHANNEL')

    # Create a Slack WebClient
    slack_client = WebClient(token=slack_token)

    # Create a Cost Explorer client
    ce_client = boto3.client('ce', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region)

    # Get the current date
    today = datetime.now()

    # Calculate the start and end dates for the previous 2 days
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=1)


    # Convert dates to the required format
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')


    # # Get the cost and usage data for the first day
    response_day1 = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date_str,
            'End': end_date_str  # Note: Start and End should be different for a valid query
        },
        Granularity='DAILY',
        Metrics=['BlendedCost']

    )

    # Print the bill for the first day
    for result in response_day1['ResultsByTime']:
        date_str_day1 = result['TimePeriod']['Start']
        total_cost_day1_str = result['Total']['BlendedCost']['Amount']
        formatted_cost_day1 = "${:.2f}".format(float(total_cost_day1_str))
        print(f"Total Blended Cost for {date_str_day1}: {formatted_cost_day1}")
        
    # Get the current date
    today = datetime.now()

    # Calculate the start and end dates for the previous day
    end_date = today - timedelta(days=0)
    start_date = end_date - timedelta(days=1)

    # Convert dates to the required format
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Get the cost and usage data for the second day
    response_day2 = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date_str,
            'End': end_date_str
        },
        Granularity='DAILY',
        Metrics=['BlendedCost']
    )

    # Print the bill for the second day
    for result in response_day2['ResultsByTime']:
        date_str_day2 = result['TimePeriod']['Start']
        total_cost_day2_str = result['Total']['BlendedCost']['Amount']
        formatted_cost_day2 = "${:.2f}".format(float(total_cost_day2_str))
        print(f"Total Blended Cost for {date_str_day2}: {formatted_cost_day2}")

    # Extract the numerical part using regular expressions
    total_cost_day1_match = re.search(r'\d+\.\d+', total_cost_day1_str)
    total_cost_day2_match = re.search(r'\d+\.\d+', total_cost_day2_str)

    # Check if matches were found
    if total_cost_day1_match and total_cost_day2_match:
        total_cost_day1 = float(total_cost_day1_match.group())
        total_cost_day2 = float(total_cost_day2_match.group())

        # Calculating the percentage change
        percentage_change = ((total_cost_day2 - total_cost_day1) / total_cost_day1) * 100

        # Determine if it's an increase or decrease
        change_status = "Increased" if total_cost_day2 > total_cost_day1 else "Decreased"

        # Prepare the message
        message = (
            f"ACCOUNT-ID = 620934872547\n"
            f"Total Cost for {date_str_day1}: {formatted_cost_day1}\n"
            f"Total Cost for {date_str_day2}: {formatted_cost_day2}\n"
            f"AWS Main Account {change_status} by {abs(percentage_change):.2f}%"
        )

        try:
            # Send the message to Slack
            response = slack_client.chat_postMessage(
                channel=slack_channel,
                text=message
            )
            print("Message sent to Slack:", response['ts'])
        except SlackApiError as e:
            print(f"Error sending message to Slack: {e.response['error']}")
    else:
        print("Couldn't extract numerical values from the strings.")


if __name__ == "__main__":
    run_aws_cost_main()