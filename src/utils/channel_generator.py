import regex
import discord
import dominate
from datetime import datetime
from markdown import markdown
from dominate.tags import *
from dominate.util import raw
from emoji import EMOJI_DATA
from utils.image_utils import emoji_to_twemoji_url
from utils.channel_definitions import *

MONTHS_OF_YEAR = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']

custom_emoji_names = regex.compile(r'(\w+)(?=:\d{18}>)')
custom_emoji_ids = regex.compile(r'(?<=<:\w+:)\d{18}')
all_emojis = regex.compile(
    "(["
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]|<:\w+:\d{18}>)")

class ChannelGenerator(dominate.document):
    def __init__(self, channel: Channel, messages: list[Message]):
        super().__init__(title=', '.join([r.username for r in channel.recipients]))

        self.emoji_cache = {}
        self.channel = channel
        self.messages = messages

    def generate_html(self):
        self.__create_headers()
        with self:
            with div(cls='chatlog'):
                for message in self.messages:
                    self.__create_message(message)

    def __create_headers(self):
        with self.head:
            link(rel='stylesheet', href='https://app.staticsave.com/discord/chatlog.css')
            link(rel='stylesheet', href='https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/styles/solarized-light.min.css')
            script(src='https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.6/highlight.min.js')
            script(src='https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.8.1/lottie.min.js')
            script(src='https://app.staticsave.com/discord/chatlog.js')

    def __create_message(self, message: Message):
        with div(cls='chatlog__message-group'):
            author: ChannelUser = message.author

            div(img(cls='chatlog__author-avatar', src=author.get_avatar_url()),
                cls='chatlog__author-avatar-container')

            with div(cls='chatlog__messages'):
                span(author.username, cls='chatlog__author-name',
                    title=f'{author.username}#{author.discriminator}')

                # if author.bot:
                #     span('BOT', cls='chatlog__bot-tag')

                timestamp = datetime.fromisoformat(message.timestamp)
                string_time = timestamp.strftime(f'%d-{MONTHS_OF_YEAR[timestamp.month - 1]}-%Y %H:%M')
                
                span(string_time, cls='chatlog__timestamp')
                with div(cls='chatlog__message', title=f'Message sent: {string_time}'):
                    if message.content:
                        with div(cls='chatlog__content'):
                            with div(cls='markdown'):
                                self.__clean_content(message.content)
                    
                    if message.embeds:
                        for embed in message.embeds:
                            self.__create_embed(embed)

                    if message.attachments:
                        for attachment in message.attachments:
                            self.__create_attachment(attachment)

                    # if message.reactions:
                    #     self.__create_reactions(message.reactions)

    @div(cls='chatlog__embed')
    def __create_embed(self, embed: discord.Embed):
        div(cls='chatlog__embed-color-pill chatlog__embed-color-pill--default')
        with div(cls='chatlog__embed-content-container'):
            if embed.author:
                with div(cls='chatlog__embed-author'):
                    img(cls='chatlog__embed-author-icon', src=embed.author.icon_url)
                    span(embed.author.name, cls='chatlog__embed-author-name')
            
            with div(cls='chatlog__embed-content'):
                with div(cls='chatlog__embed-text'):
                    if embed.title:
                        with div(cls='chatlog__embed-title'):
                            link = a(cls='chatlog__embed-title-link')
                            link.add(div(embed.title, cls='markdown preserve-whitespace'))
                            if embed.url:
                                link.set_attribute('href', embed.url)

                    if embed.description:
                        with div(cls='chatlog__embed-description'):
                            div(raw(self.__apply_markdown(embed.description)), cls='markdown preserve-whitespace')
                    
                    if embed.fields:
                        with article(cls='chatlog__embed-fields'):
                            for field in embed.fields:
                                with div(cls=f'chatlog__embed-field{"--inline" if field.inline else ""}'):
                                    div(field.name, cls='chatlog__embed-field-name')
                                    div(raw(self.__apply_markdown(field.value)), cls='chatlog__embed-field-value')

                        if embed.footer:
                            footer = embed.footer
                            with div(cls='chatlog__embed-footer'):
                                if footer.icon_url:
                                    img(cls='chatlog__embed-footer-icon', src=footer.icon_url)
                                if footer.text:
                                    div(footer.text, cls='chatlog__embed-footer-text')

                if embed.thumbnail:
                    with div(cls='chatlog__embed-thumbnail-container'):
                        a(cls='chatlog__embed-thumbnail-link', href=embed.thumbnail.url) \
                            .add(img(cls='chatlog__embed-thumbnail', src=embed.thumbnail.url))
                
                if embed.image:
                    with div(cls='chatlog__embed-image-container'):
                        img(cls='chatlog__embed-image', src=embed.image.url)
    
    @div(cls='chatlog__attachment')
    def __create_attachment(self, attachment: discord.Attachment):
        if attachment.is_spoiler():
            attr(onclick='showSpoiler(event, this)')
            div('SPOILER', cls='chatlog__attachment-spoiler-caption')
        with a(href=attachment.url):
            content_type: str = attachment.content_type
            if not content_type:
                tag = img
            else:
                tag = img if content_type.startswith('image') else video if content_type.startswith('video') else img
            tag(cls='chatlog__attachment-media', src=attachment.url, alt=attachment.filename, title=f'{attachment.filename} ({attachment.size / 1000} KB)', loading='lazy')
    
    @div(cls='chatlog__reactions')
    def __create_reactions(self, reactions):
        for reaction in reactions:
            with div(cls='chatlog__reaction', title=''):
                self.__create_emoji(reaction.emoji, True, not (reaction.emoji in EMOJI_DATA))
                span(reaction.count, cls='chatlog__reaction-count')
    
    def __create_emoji(self, emoji, is_reaction, is_custom):
        cached_emoji = self.__search_cache(emoji, is_reaction, is_custom)
        if cached_emoji:
            return cached_emoji

        url = None
        try:
            if is_custom:
                emoji_id = custom_emoji_ids.findall(emoji)[0] if not is_reaction else emoji.id
                url = f'https://cdn.discordapp.com/emojis/{emoji_id}.webp'
            else:
                url = emoji_to_twemoji_url(emoji)
            emoji_name = emoji if not is_custom else custom_emoji_names.findall(emoji)[0] if not is_reaction else emoji.name
        except:
            self.emoji_cache[(emoji, is_reaction, is_custom)] = emoji
            return emoji

        tag = img(cls=f'emoji{"--small" if is_reaction else ""}', src=url, loading='lazy', alt=emoji_name) 
        self.emoji_cache[(emoji, is_reaction, is_custom)] = tag
        return tag

    def __clean_content(self, content: str):
        emojis = list(set(all_emojis.findall(content)))
        clean_text = [content]

        for emoji in emojis:
            clean_text, success = self.__split_text(clean_text, emoji)
            if success:
                temp = clean_text.copy()
                idx = 0
                for i, t in enumerate(temp):
                    if i == len(temp) - 1:
                        break

                    idx = clean_text.index(t, idx + (1 if idx > 0 else 0))
                    is_valid = (idx < len(clean_text))
                    is_same_type = (type(clean_text[idx]) == type(clean_text[idx + 1]))
                    is_type_str = (type(clean_text[idx]) == str)

                    if is_valid and is_same_type and is_type_str:
                        is_custom = not (emoji in EMOJI_DATA)
                        new_emoji = self.__create_emoji(emoji, False, is_custom)

                        clean_text[idx+1:idx+1] = [new_emoji]
        
        temp_copy = clean_text.copy()
        for i, element in enumerate(temp_copy):
            if type(element) != str:
                continue
                
            clean_text.pop(i)
            clean_text.insert(i, raw(self.__apply_markdown(element)))

        span(*clean_text, cls='preserve-whitepsace')

    def __split_text(self, text_array: list[str], split_char: str):
        temp_array = text_array.copy()
        old_size = len(text_array)

        for text in temp_array:
            if type(text) != str:
                continue

            split_text = text.split(split_char)

            if not len(split_text) > 1:
                continue

            idx = text_array.index(text)
            text_array.pop(idx)
            text_array[idx:idx] = split_text

        return text_array, old_size is not len(text_array)

    def __apply_markdown(self, string: str):
        return markdown(string)[3:-4]

    def __search_cache(self, emoji, is_reaction, is_custom):
        q = (emoji, is_reaction, is_custom)
        if q in self.emoji_cache:
            return self.emoji_cache[q]
        return None
        