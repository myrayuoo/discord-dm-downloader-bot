import os
import toml
import json
from os import path
from dotenv import load_dotenv
from utils.channel_definitions import *
from utils.channel_generator import ChannelGenerator

load_dotenv('.builder.env')


class UserData:
    def __init__(self, id: str, is_incomplete: bool = False) -> None:
        self.id = id
        self.is_incomplete = is_incomplete


ROOT_DIR = os.getenv('ROOT_DIR')
OUTPUT_DIR = os.getenv('OUTPUT_DIR')

if not path.exists(ROOT_DIR):
    raise Exception('Unable to locate root director. check your .builder.env file.')

if not path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

global_config = {}
with open(ROOT_DIR + '/config.toml', 'r') as file:
    global_config = toml.load(file)

users_data: list[UserData] = []
for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
    for user_dir in dirnames:
        users_data.append(UserData(user_dir, global_config.get('in_progress', '') == user_dir))
    break

if not users_data:
    raise Exception('No user data found.')

print('Choose a user to build:')
for index, user_data in enumerate(users_data):
    print(f'\t{index+1}) {user_data.id} {f"(incomplete)" if user_data.is_incomplete else ""}')

choice = int(input())
choice_count = len(users_data) 
if choice <= 0 or choice > choice_count:
    raise ValueError('Invalid choice.')
chosen_user = users_data[index-1]

USER_DATA_PATH = ROOT_DIR + '/' + chosen_user.id

with open(USER_DATA_PATH + '/channels.json', 'r') as file:
    unparsed_channels = json.load(file)

channels: list[Channel] = [Channel(
    id=uc['id'],
    last_message_id=uc['last_message_id'],
    recipients=[ChannelUser(
        id=cu['id'],
        username=cu['username'],
        avatar=cu['avatar'],
        discriminator=cu['discriminator']
    ) for cu in uc['recipients']]
) for uc in unparsed_channels]

for dirpath, dirnames, filenames in os.walk(USER_DATA_PATH):
    for channel_dir in dirnames:
        CHANNEL_DATA_FILE = USER_DATA_PATH + '/' + channel_dir + '/data.json'
        if not path.exists(CHANNEL_DATA_FILE):
            print(f"Data file '{channel_dir}' doesn't exist, skipping.")
            continue

        unparsed_messages = []
        with open(CHANNEL_DATA_FILE, 'r') as file:
            unparsed_messages = [json.loads(um) for um in file.readlines()]
        
        messages: list[Message] = [Message(
            id=m['id'],
            content=m['content'],
            channel_id=m['channel_id'],
            author=ChannelUser(**m['author']),
            attachments=[discord.Attachment(data=a, state=FakeConnectionState()) for a in m['attachments']],
            embeds=[discord.Embed.from_dict(e) for e in m['embeds']],
            reactions=[],
            timestamp=m['timestamp'],
            edited_timestamp=m['edited_timestamp']
        ) for m in unparsed_messages]

        filtered_channels = list(filter(lambda c: c.id == channel_dir, channels))
        if not filtered_channels:
            print('could not find channel, skipping')
            continue

        channel: Channel = filtered_channels[0]
        generator: ChannelGenerator = ChannelGenerator(channel, messages)
        print('building', channel.id)
        generator.generate_html()
        
        OUT_FILE = OUTPUT_DIR + f'/{channel.id}.html'

        with open(OUT_FILE, 'wb+') as file:
            file.write(generator.render().encode('utf-8'))
        
        print('Written to:', OUT_FILE)
