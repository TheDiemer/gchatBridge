# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=invalid-name
"""
Hangouts Chat bot that responds to events and messages from a room asynchronously.
"""

# [START async-bot]


import logging
from googleapiclient.discovery import build
from flask import Flask, render_template, request, json
import google.auth
import requests
import json

app = Flask(__name__)

scopes = ['https://www.googleapis.com/auth/chat.bot']
credentials, project_id = google.auth.default()
credentials = credentials.with_scopes(scopes=scopes)
chat = build('chat', 'v1', credentials=credentials)


@app.route('/', methods=['POST'])
def home_post():
    """Respond to POST requests to this endpoint.

    All requests sent to this endpoint from Hangouts Chat are POST
    requests.
    """

    event_data = request.get_json()

    resp = None
    print(event_data)

    # If the bot is removed from the space, it doesn't post a message
    # to the space. Instead, log a message showing that the bot was removed.
    if event_data['type'] == 'REMOVED_FROM_SPACE':
        logging.info('Bot removed from  %s', event_data['space']['name'])
        return json.dumps({})

    resp = format_response(event_data)
    space_name = event_data['space']['name']
    send_async_response(resp, space_name)

    # Return empty jsom respomse simce message already sent via REST API
    return json.dumps({})

# [START async-response]

def send_async_response(response, space_name):
    """Sends a response back to the Hangouts Chat room asynchronously.

    Args:
      response: the response payload
      space_name: The URL of the Hangouts Chat room

    """
    chat.spaces().messages().create(
        parent=space_name,
        body=response).execute()

# [END async-response]

def format_response(event):
    """Determine what response to provide based upon event data.

    Args:
      event: A dictionary with the event data.

    """

    event_type = event['type']

    text = ""
    sender_name = event['user']['displayName']

    # Case 1: The bot was added to a room
    if event_type == 'ADDED_TO_SPACE' and event['space']['type'] == 'ROOM':
        text = 'Thanks for adding me to {}!'.format(event['space']['displayName'])

    # Case 2: The bot was added to a DM
    elif event_type == 'ADDED_TO_SPACE' and event['space']['type'] == 'DM':
        text = 'Thanks for adding me to a DM, {}!'.format(sender_name)

    elif event_type == 'MESSAGE':
        sent = slackOrIRC(event['message']['text'], event['message']['sender']['displayName'])
        if sent[0]:
            if sent[1]:
                text = 'Thanks for engaging! Your message to {0} has been sent successfully!'.format(sent[2])
            else:
                text = 'Thanks for engaging! For some reason I couldn\'t send your message to {0}.\nPlease try again!'.format(sent[2])
        else:
            text = 'Sorry, this bot is limited to sending messages to irc or slack! Please specify which one of those you\'d like to send a message in before a newline and your message!'

    response = {'text': text}

    # The following three lines of code update the thread that raised the event.
    # Delete them if you want to send the message in a new thread.
    if event_type == 'MESSAGE' and event['message']['thread'] is not None:
        thread_id = event['message']['thread']
        response['thread'] = thread_id

    return response

# [END async-bot]


def slackOrIRC(message, sender):
    # We will send back a list called sent
    # sent = [Bool1, Bool2, String]
    # Bool1 = Whether they specified irc or slack
    # Bool2 = If the message was sent successfully or not
    # String = irc or slack
    if ' irc\n' in message.lower():
        sent = [True, False, "irc"]
    elif ' slack\n' in message.lower():
        sent = [True, False, "slack"]
    else:
        sent = [False, False, None]
        return sent

    messageparts = message.split("\n")
    newMessage = ' '.join(messageparts[1:])

    if sent[2] == "irc":
        msg = "<@UQBA90P1R> irc\n{0} said: {1}".format(sender, newMessage)
    else:
        msg = "@sre-ic {0} said: {1}".format(sender, newMessage)
    data = {"text": msg}

    r = requests.post('https://hooks.slack.com/services/' + 'T027F3GAJ/BQNCN3G3W/VnrFHebh0mDUpPPWqkhuuh7n', headers={'Content-type':'application/json'}, data=json.dumps(data))
    if r.status_code == 200:
        sent[1] = True

    return sent


@app.route('/', methods=['GET'])
def home_get():
    """Respond to GET requests to this endpoint.

    This function responds to requests with a simple HTML landing page for this
    App Engine instance.
    """

    return render_template('home.html')


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    #app.run(host='127.0.0.1', port=8080, debug=True)
    app.run(host='0.0.0.0',port=8080, debug=True)
