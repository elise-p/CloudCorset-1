from datetime import datetime
from dateutil import tz
import boto3

# Check which cities is currently 6-7 am and check if there is users in those cities
# If there is one, ping the getOutfit.py to generate outfit

dynamodb = boto3.client('dynamodb')
TABLE_NAME = '' # dynamodb table name (intentionally deleted for public)

city_timezones = {
    "Tokyo": "Asia/Tokyo",
    "London": "Europe/London",
    "Jakarta": "Asia/Jakarta",
    "New York": "America/New_York",
    "Sydney": "Australia/Sydney"
}

def lambda_handler(event, context):
    result = []
    for city, timezone_str in city_timezones.items():
        tzinfo = tz.gettz(timezone_str)
        now = datetime.now(tz=tzinfo)
        if 6 <= now.hour < 7:
            users = dynamodb.scan(
                TableName=TABLE_NAME,
                FilterExpression="user_city = :c",
                ExpressionAttributeValues={":c": {"S": city}}
            )
            if users['Count'] > 0:
                result.append(city)

    if not result:
        return {"stopExecution": True}

    return {"stopExecution": False, "cities": result}
