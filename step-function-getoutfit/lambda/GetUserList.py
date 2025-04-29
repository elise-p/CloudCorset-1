import os
import json
import boto3
import urllib.request
import urllib.parse
import base64

# DynamoDB setup
dynamodb = boto3.client('dynamodb')
TABLE_NAME = '' # intentionally redacted.

# Mailgun email sender
def send_email(to, subject, body):
    api_key = os.environ.get("mailgun_api_key")
    domain = "eliseponiman.me"

    if not api_key:
        print("API Key not found!")
        return False

    mailgun_url = f"https://api.mailgun.net/v3/{domain}/messages"

    post_data = urllib.parse.urlencode({
        "from": f"CloudCorset <cloudcorset@{domain}>",
        "to": to,
        "subject": subject,
        "text": body
    }).encode("utf-8")

    auth_string = f"api:{api_key}"
    base64_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    request = urllib.request.Request(mailgun_url, data=post_data)
    request.add_header("Authorization", f"Basic {base64_auth}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print(f"Email sent to {to}")
                return True
            else:
                print(f"Failed to send email to {to}. Status Code: {response.status}")
                return False
    except urllib.error.HTTPError as e:
        print(f"HTTPError for {to}: {e.code} - {e.reason}")
        print(e.read().decode())
        return False
    except urllib.error.URLError as e:
        print(f"URLError for {to}: {e.reason}")
        return False

# Group time blocks with the same outfit description
def group_forecast_blocks(city_forecast, skip_keys):
    grouped_blocks = []
    temp_blocks = []

    for time_range, desc in city_forecast.items():
        if time_range in skip_keys:
            continue
        start, end = [int(t.replace(":", "")) for t in time_range.split(" - ")]
        temp_blocks.append((start, end, desc))

    temp_blocks.sort()

    i = 0
    while i < len(temp_blocks):
        start = temp_blocks[i][0]
        end = temp_blocks[i][1]
        desc = temp_blocks[i][2]

        j = i + 1
        while j < len(temp_blocks) and temp_blocks[j][2] == desc and temp_blocks[j][0] == end:
            end = temp_blocks[j][1]
            j += 1

        # turn start and end into 4-digit strings so it's easier to split into hours and minutes
        start_str = f"{start:04d}"
        end_str = f"{end:04d}"

        # format it into the final "- start - end → description" style
        formatted_block = f"- {start_str[:2]}:{start_str[2:]} - {end_str[:2]}:{end_str[2:]} → {desc}"

        # add this formatted block into the list
        grouped_blocks.append(formatted_block)

        i = j

    return grouped_blocks

# Lambda entry point
# Generate the email to be sent to users
def lambda_handler(event, context):
    cities = event.get("cities", [])
    weather_map = event.get("outfit_map", {})

    if not cities:
        return { "emails": [] }

    # Build expression for city filtering
    expr_values = {}
    expr_keys = []
    for i, city in enumerate(cities):
        key = f":city{i}"
        expr_keys.append(key)
        expr_values[key] = { "S": city }

    filter_expr = f"user_city IN ({', '.join(expr_keys)})"

    response = dynamodb.scan(
        TableName=TABLE_NAME,
        FilterExpression=filter_expr,
        ExpressionAttributeValues=expr_values
    )

    users = response.get("Items", [])
    emails = []

    for user in users:
        city = user["user_city"]["S"]
        name = user["user_name"]["S"]
        email = user["user_email"]["S"]
        forecast = weather_map.get(city)

        msg_lines = [
            f"Hi {name},",
            "",
            f"Here’s your outfit recommendation for {city} today:"
        ]

        if forecast:
            always_show_keys = ["09:00 - 18:00", "09:00 - 21:00"]
            summary_lines = [
                f"- {key} → {forecast[key]}"
                for key in always_show_keys if key in forecast
            ]
            breakdown_lines = group_forecast_blocks(forecast, skip_keys=set(always_show_keys))

            if summary_lines:
                msg_lines.append("\nSummary:")
                msg_lines.extend(summary_lines)

            if breakdown_lines:
                msg_lines.append("\nBy Time Block:")
                msg_lines.extend(breakdown_lines)
        else:
            msg_lines.append("Forecast data not available.")

        msg_lines.append("\nStay comfy and dress accordingly! 😊")
        body = "\n".join(msg_lines)
        subject = f"Your {city} Weather Update 🌤️"

        send_email(email, subject, body)

        emails.append({
            "to": email,
            "subject": subject,
            "body": body
        })

    return { "emails": emails }
