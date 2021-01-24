import json

from twilio.rest import Client

CREDS = json.load(open('creds.json', 'r'))

client = Client(**CREDS)

call = client.calls.create(
    url='http://demo.twilio.com/docs/voice.xml',
    to='+12027654168',
    from_='+19514194490'
)

print(call.sid)