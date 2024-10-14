import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
import traceback
import sqlite3

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') # requires OpenAI Realtime API Access
PORT = int(os.getenv('PORT', 5050))
#  SYSTEM_MESSAGE = (
#     "You are a helpful assistant for a salon and enbles the user to make and cancel appointments. You follow the following instructions."
#     "Greet the user and ask from their name. The user "
#     "Ask the user about a time of appointment today - you can only book appointments for today."
#     "Next, ask the user if they want to book a Premium Cut or an Express Cut"
#     "You must ask the user a question one by one ONLY. If you have obtained all the information - do not repeat"
#     "the question."
#     "Once you have all the information about user, time and service type, you get the hair care specialists available"
#     "at that slot using get_available_specialists."
#     "You prompt the user to confirm the hair care specialist they want to book with from the available options."
#     "Once the user confirms the specialist, you book an appointment for that specialist using book_appointment tools"
#     "ONLY book the apppoinment once the user confirms the speicalist."
#     "Give the user flexible options if he expresses hesitance in booking e.g. offering to book with other specialists or explore more options."
#     "Note that the tools expect time stamps in absolute time, so you should convert AM/PM slots to appopriate times"
#     "before invoking tools. E.g. using 14:00 instead of 2 PM, or 17:00 instead of 5 PM"
# )

SYSTEM_MESSAGE = (
    """"
    You are a helpful assistant for a salon and enables the user to make and cancel appointments. 
    Greet the user with energy and ask them explain that you can help with either booking or canceling appointments.
    The appointment booking and cancellation flows are listed below

    Appointment Booking flow

    Greet the user and ask from their name.
    Ask the user about a time of appointment today - you can only book appointments for today. 
    Next, ask the user if they want to book a Premium Cut or an Express Cut You must ask the user a question one by one ONLY. 
    If you have obtained all the information - do not repeat the question. 
    Once you have all the information about user, time and service type, you get the hair care specialists available at that slot using get_available_specialists. 
    You prompt the user to confirm the hair care specialist they want to book with from the available options. 
    Once the user confirms the specialist, you book an appointment for that specialist using book_appointment tools.
    ONLY book the appointment once the user confirms the specialist. 
    Note that the tools expect time stamps in absolute time, so you should convert AM/PM slots to appropriate times before invoking tools. 
    E.g. using 14:00 instead of 2 PM, or 17:00 instead of 5 PM.

    Appointment Cancellation Flow

    TODO


    """

)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

#TOOLS = [
#   {
#     "type": "function",
#     "name": "get_weather",
#     "description": "Get the weather at a given location",
#     "parameters": {
#       "type": "object",
#       "properties": {
#         "location": {
#           "type": "string",
#           "description": "Location to get the weather from"
#         }
#       },
#       "required": ["location"]
#     }
#   }
#]

TOOLS = [
    {
        "type": "function",
        "name": "book_appointment",
        "description": "Book appointments at a slot",
        "parameters": {
        "type": "object",
        "properties": {
            "slot": {
            "type": "string",
            "description": "Slot for the appointment"
            },
            "service_type": {
            "type": "string",
            "description": "Type of Service to book for"
            },
            "user_name": {
            "type": "string",
            "description": "Name of the user"
            },
            "specialist_name": {
            "type": "string",
            "description": "Name of the specialist for the appointment"
            }
        },
        "required": ["slot", "service_type", "user_name", "specialist_name"]
        }
    }, 

    {
        "type": "function",
        "name": "get_available_specialists",
        "description": "Get Available Specialists at a slot",
        "parameters": {
        "type": "object",
        "properties": {
            "slot": {
            "type": "string",
            "description": "Slot for the appointment"
            },
            "service_type": {
            "type": "string",
            "description": "Type of Service to book for",
            "enum": ["Premium", "Express"]
            },
        },
        "required": ["slot", "service_type"]
        }
    },

    {
        "type": "function",
        "name": "get_all_specialists",
        "description": "Get the name of all specialists"
    }
]


def book_appointment(user_name: str, specialist_name: str, slot: str, service_type: str):
    print(f"Booking appointment at slot {slot} for {specialist_name} for {user_name}")
    # return {
    #     "status": "Booked",
    #     #"availble": ["Alice", "Bob"]
    # }
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Update the status to 'Booked' and set the booked_by field with the user's name
    cursor.execute('''
        UPDATE appointment
        SET status = 'Booked', booked_by = ?
        WHERE name = ? AND time = ? AND service = ? AND status = 'Free'
    ''', (user_name, specialist_name, slot, service_type))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    # Check if any rows were updated (meaning the specialist was available and now booked)
    if cursor.rowcount == 0:
        return "No available specialist found for the given details."
    else:
        print(f"{specialist_name} has been booked for {slot} providing {service_type} service.")
        return "Success"



def get_available_specialists(slot: str, service_type: str):
    # Connect to the SQLite database
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    # Query to get the specialists available for the given slot and service type
    cursor.execute('''
        SELECT name FROM appointment
        WHERE time = ? AND service = ? AND status = 'Free'
    ''', (slot, service_type))
    
    # Fetch all available specialists
    available_specialists = cursor.fetchall()
    
    # Close the connection
    conn.close()
    
    # Convert list of tuples to a simple list
    specialists = [specialist[0] for specialist in available_specialists]
    print(f"Retrieved data from the database {specialists}")
    return specialists
    # return {
    #     #"status": "success",
    #     "available": ["Alice", "Bob"]
    # }


# Function to get all unique specialist names from the database
def get_all_specialist_names():
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        # SQL query to select all unique specialist names
        cursor.execute('SELECT DISTINCT name FROM appointment')

        # Fetch all results
        specialists = cursor.fetchall()

        # Convert the list of tuples into a simple list
        specialist_names = [row[0] for row in specialists]

        return specialist_names

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# def get_weather(location: str):
#     #return f"The weather is pretty good at {location}"
#     return {"temperature" : "59F"}

functions = {
        #"get_weather": get_weather,
        "book_appointment": book_appointment,
        "get_available_specialists": get_available_specialists,
        "get_all_specialist_names": get_all_specialist_names
    }

app = FastAPI()


if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

@app.get("/", response_class=HTMLResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    print("here")
    # <Say> punctuation to improve text-to-speech flow
    #response.say("Connecting your call.")
    #response.pause(length=1)
    #response.say("O.K. you can start talking!")
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await send_session_update(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            print("Receiving from metadata")
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            print("Sending to twilio")
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)
                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)
                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        # Audio from OpenAI
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
                    if response['type'] == 'response.done':
                        if response.get('response', {}).get('output') is not None:
                            outputs = response.get('response').get('output')
                            for item in outputs:
                                #first_item = response.get('response').get('output')[0]
                                if item.get('type') == 'function_call':
                                    name = item.get('name')
                                    args = json.loads(item.get('arguments'))
                                    #import ipdb; ipdb.set_trace()
                                    if name in functions:
                                        output = functions[name](**args)
                                        print(f"Output here is {output}")
                                        await openai_ws.send(
                                            json.dumps(
                                                    {
                                                        "type": "conversation.item.create",
                                                        "item": {
                                                            "type": "message",
                                                            "role": "user",
                                                            "content": [{"type": "input_text", "text": str(output)}],
                                                        },
                                                    }
                                                )
                                        )
                                        await openai_ws.send(json.dumps({"type": "response.create"}))
                                #print(f"Extracted output as {output}")
            except Exception as e:
                traceback.print_exc()
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_session_update(openai_ws):
    """Send session update to OpenAI WebSocket."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools": TOOLS,
            "tool_choice": "auto"
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)