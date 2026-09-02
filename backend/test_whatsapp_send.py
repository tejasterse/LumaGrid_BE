import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])

message = client.messages.create(
    from_=os.environ["TWILIO_WHATSAPP_NUMBER"],
    to="whatsapp:+919049156979",  # the exact number you used to join the sandbox
    content_sid="HXfe5ab5f00277942d4d4200328b4d403c"
)

print("Sent. SID:", message.sid)