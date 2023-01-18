import os
import toml
import time
import json
import shutil
import argparse
import requests
from os import path
from dotenv import load_dotenv
from utils.channel_definitions import *
import math
# download dms
# approach:
#   - iterate in order
#   - each channel has a separate folder containing:
#       - progress.conf
#       - data.json
#
#   structure:
#       -dl
#           -<userid>
#               -profile.json
#               -<channelid>
#                   -progress.conf
#                   -data.json
#
#
#   - in each sub iteration write to file (eg. messages chunck, last message id)

# all unnecessary stuff are not included in classes


parser = argparse.ArgumentParser(
    prog='DM Download Bot',
    description='Downloads messages from dms.',
    epilog='This program is a proof of concept and is for educational purposes only.'
)
parser.add_argument('-t', '--token', help='Target user token', required=True)

args = parser.parse_args()

load_dotenv(dotenv_path='.downloader.env')

BASE_URL = 'https://discord.com/api/v9'
ME_ENDPOINT = BASE_URL + '/users/@me'
DM_CHANNELS_ENDPOINT = BASE_URL + '/users/@me/channels'
CHANNEL_MESSAGES_ENDPOINT = BASE_URL + '/channels/<id>/messages'

TOKEN = args.token
 
CONFIG_FILE = os.getenv('CONFIG_FILE')
CHANNEL_MAX_MESSAGES_DOWNLOAD = int(os.getenv('CHANNEL_MAX_MESSAGES_DOWNLOAD'))

headers = {'Authorization': TOKEN}

def start_fresh():
    if not path.exists('dl'):
        os.mkdir('dl')

    profile_res = requests.get(ME_ENDPOINT, headers=headers)

    if not profile_res.ok:
        raise Exception('Fetching profile failed')

    profile = profile_res.json()
    profile['token'] = TOKEN # just in case

    USER_DL_PATH = f'./dl/{profile["id"]}'
    if not path.exists(USER_DL_PATH):
        os.mkdir(USER_DL_PATH)

    with open(USER_DL_PATH + '/profile.json', 'w+') as file:
        json.dump(profile, file)

    channels_res = requests.get(DM_CHANNELS_ENDPOINT, headers=headers)

    if not channels_res.ok:
        raise Exception('Fetching dm channels failed')

    channels_unstructured = channels_res.json()

    with open(USER_DL_PATH + '/channels.json', 'w+') as file:
        json.dump(channels_unstructured, file)

    global_config = {'in_progress': profile['id']}
    with open(CONFIG_FILE, 'w+') as file:
        toml.dump(global_config, file)

    channel_config = {'in_progress': None}

    channels: list[Channel] = []
    for uc in channels_unstructured:
        channel = Channel(
            id=uc['id'],
            last_message_id=uc['last_message_id'],
            recipients=[ChannelUser(
                id=r['id'],
                username=r['username'],
                avatar=r['avatar'],
                discriminator=r['discriminator']
            ) for r in uc['recipients']]
        )
        channels.append(channel)

        channel_config['in_progress'] = channel.id
        with open(USER_DL_PATH + '/config.toml', 'w+') as file:
            toml.dump(channel_config, file)

        NEW_CHANNEL_PATH = USER_DL_PATH + '/' + channel.id
        if not path.exists(NEW_CHANNEL_PATH):
            os.mkdir(NEW_CHANNEL_PATH)
        LOCAL_CONF_FILE = NEW_CHANNEL_PATH + '/progress.toml'

        data = []
        local_config = {}
        last_fetch_message_id = channel.last_message_id
        num_of_fetches = 0
        max_fetches = math.ceil(CHANNEL_MAX_MESSAGES_DOWNLOAD / 100) + 1
        with open(LOCAL_CONF_FILE, 'w+') as conf_file:
            with open(NEW_CHANNEL_PATH + '/data.json', 'a+') as file:
                while len(data) <= CHANNEL_MAX_MESSAGES_DOWNLOAD:
                    if not last_fetch_message_id or num_of_fetches >= max_fetches:
                        break

                    if data:
                        if last_fetch_message_id == data[-1]['id']:
                            break

                        last_fetch_message_id = data[-1]['id']
                    elif not data and num_of_fetches > 2:
                        break

                    local_config['last_fetched_message_id'] = last_fetch_message_id
                    conf_file.truncate()
                    conf_file.seek(0)
                    toml.dump(local_config, conf_file)

                    req_url = CHANNEL_MESSAGES_ENDPOINT.replace(
                        '<id>', channel.id) + f'?limit=100&before={last_fetch_message_id}'
                    messages_res = requests.get(req_url,
                                                headers=headers)
                    match messages_res.status_code:
                        case 200:
                            print('fetched messages')
                            messages = messages_res.json()
                            data += messages
                            for message in messages:
                                json.dump(message, file)
                                file.write('\n')

                        case _:
                            print(messages_res)
                    num_of_fetches += 1

        print('finished channel')
        local_config['last_fetched_message_id'] = None
        with open(LOCAL_CONF_FILE, 'w+') as file:
            toml.dump(local_config, file)
        
    channel_config['in_progress'] = None
    with open(USER_DL_PATH + '/config.toml', 'w+') as file:
        toml.dump(channel_config, file)

    global_config = {'in_progress': None}
    with open(CONFIG_FILE, 'w+') as file:
        toml.dump(global_config, file)


# not completing it
def continue_download():
    pass

if not path.exists('./dl') or not path.isfile(CONFIG_FILE):
    start_fresh()

continue_download()