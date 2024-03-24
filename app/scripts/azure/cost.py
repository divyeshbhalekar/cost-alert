import requests
import os
from datetime import datetime, timedelta
from jinja2 import Template
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

def run_azure_cost():
    # Load environment variables from .env
    load_dotenv()

    # Specify your Slack API token and channel
    slack_token = os.environ.get('SLACK_TOKEN')
    slack_channel = os.environ.get('SLACK_CHANNEL')

    # Create a Slack WebClient
    slack_client = WebClient(token=slack_token)

    subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
    tenant_id = os.environ.get('AZURE_TENANT_ID')
    client_id = os.environ.get('AZURE_CLIENT_ID')
    client_secret = os.environ.get('AZURE_CLIENT_SECRET')

    # Authenticate with Azure AD and get access token
    auth_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': 'https://management.azure.com/'
    }
    auth_response = requests.post(auth_url, data=auth_data)
    access_token = auth_response.json()['access_token']

    usage_url = f'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2019-11-01'
    usage_data = {
        'type': 'Usage',
        'timeframe': 'Custom',
        'timePeriod': {
            'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z'),
            'to': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT23:59:59Z')
        },
        'dataset': {
            'granularity': 'Daily',
            'aggregation': {
                'totalCost': {
                    'name': 'Cost',
                    'function': 'Sum'
                }
            },
            'grouping': [
                {
                    'type': 'Dimension',
                    'name': 'ServiceName'
                }
            ]
        }
    }

    today = datetime.now() - timedelta(days=1)
    start_of_month = datetime(today.year, today.month, 1).strftime('%Y-%m-%dT00:00:00Z')
    end_of_month = (datetime(today.year, today.month+1, 1) - timedelta(days=1)).strftime('%Y-%m-%dT23:59:59Z')

    usage_data_2 = {
        'type': 'Usage',
        'timeframe': 'Custom',
        'timePeriod': {
            'from': start_of_month,
            'to': end_of_month
        },
        'dataset': {
            'granularity': 'Monthly',
            'aggregation': {
                'totalCost': {
                    'name': 'Cost',
                    'function': 'Sum'
                }
            },
            'grouping': [
                {
                    'type': 'Dimension',
                    'name': 'ServiceName'
                }
            ]
        }
    }

    # date2
    usage_data_7 = {
        'type': 'Usage',
        'timeframe': 'Custom',
        'timePeriod': {
            'from': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%dT00:00:00Z'),
            'to': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%dT23:59:59Z')
        },
        'dataset': {
            'granularity': 'Daily',
            'aggregation': {
                'totalCost': {
                    'name': 'Cost',
                    'function': 'Sum'
                }
            },
            'grouping': [
                {
                    'type': 'Dimension',
                    'name': 'ServiceName'
                }
            ]
        }
    }

    usage_response = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data)
    usage_response_2 = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_2)
    usage_response_7 = requests.post(usage_url, headers={'Authorization': f'Bearer {access_token}'}, json=usage_data_7)


    cost_data = usage_response.json()['properties']['rows']
    cost_data_7 = usage_response_7.json()['properties']['rows']

    # for Monthly
    cost_data_M = usage_response_2.json()['properties']['rows']
    total_cost_M = sum([row[0] for row in cost_data_M])
    monthly_budget = 40000  # 5 lakh INR
    percent_consumed = (total_cost_M / monthly_budget) * 100

    cost_data = [
        {
            'cost': row[0],
            'date': row[1],
            'service': row[2],
            'currency': row[3]
        }
        for row in cost_data
    ]

    total_cost = 0
    total_cost_date = None
    for row in cost_data:
        if total_cost_date is None or row['date'] > total_cost_date:
            total_cost_date = row['date']
            date_obj = datetime.strptime(str(total_cost_date), "%Y%m%d")
            total_cost_date_1 = date_obj.strftime("%Y-%m-%d")
        total_cost += row['cost']

    cost_data_sorted = sorted(cost_data, key=lambda k: k['cost'], reverse=True)

    # code for 2nd day cost
    cost_data_7 = [
        {
            'cost': row[0],
            'date': row[1],
            'service': row[2],
            'currency': row[3]
        }
        for row in cost_data_7
    ]

    total_cost_7 = 0
    total_cost_date_7 = None
    for row in cost_data_7:
        if total_cost_date_7 is None or row['date'] > total_cost_date_7:
            total_cost_date_7 = row['date']
            date_obj_7 = datetime.strptime(str(total_cost_date_7), "%Y%m%d")
            total_cost_date_3 = date_obj_7.strftime("%Y-%m-%d")
        total_cost_7 += row['cost']

    cost_data_sorted_1 = sorted(cost_data_7, key=lambda k: k['cost'], reverse=True)

    percentage_change = ((total_cost_7 - total_cost) / total_cost) * 100
    # Determine if it's an increase or decrease
    change_status = "Increased" if total_cost_7 > total_cost else "Decreased"

    # Send the output to the Slack channel
    try:
        message = (
            f'AZURE ACCOUNT COST\n'
            f'Total cost on {total_cost_date_1}: {total_cost:.2f} {cost_data[0]["currency"]}\n'
            f'Total cost on {total_cost_date_3}: {total_cost_7:.2f} {cost_data_7[0]["currency"]}\n'
            f'AZURE Account  {change_status} by {abs(percentage_change):.2f}%\n'
            f'Total cost for current month: {total_cost_M:.2f} INR\n'
            f'Percentage of monthly budget consumed so far: {percent_consumed:.2f}%\n\n'
            f'Top 5 services by cost for {total_cost_date_1}:\n'
        )
        for i, row in enumerate(cost_data_sorted[:6]):
            message += f"{i+1}. {row['service']} - {row['cost']:.2f} {row['currency']}\n"

        response = slack_client.chat_postMessage(channel=slack_channel, text=message)
        assert response["message"]["text"] == message
        print("Message sent successfully to Slack channel.")
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")

if __name__ == "__main__":
    run_azure_cost()