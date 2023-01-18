import discord


class ChannelUser:
    def __init__(self, id: str = None, username: str = None, avatar: str = None, discriminator: str = None, **kwargs) -> None:
        self.id = id
        self.username = username
        self.avatar = avatar
        self.discriminator = discriminator

    def get_avatar_url(self):
        return f'https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}'

    def __repr__(self) -> str:
        return f'<ChannelUser id={self.id} username="{self.username}" avatar="{self.avatar}" discriminator={self.discriminator}>'

    def __str__(self) -> str:
        return self.__repr__()


class Channel:
    def __init__(self, id: str = None, last_message_id: str | None = None, recipients: list[ChannelUser] = [], **kwargs) -> None:
        self.id = id
        self.last_message_id = last_message_id
        self.recipients = recipients

    def _set_recipents(self, recipients: list[ChannelUser]):
        self.recipients = recipients

    def __repr__(self) -> str:
        return f'<Channel id={self.id} last_message_id={self.last_message_id}\n' + \
            f'\recipients="{self.recipients}">'

    def __str__(self) -> str:
        return self.__repr__()


class EmbedThumbnail:
    def __init__(self, url: str = None, proxy_url: str = None, **kwargs) -> None:
        self.url = url
        self.proxy_url = proxy_url


class Embed:
    def __init__(self,
                 type: str = None,
                 url: str = None,
                 title: str = None,
                 description: str = None,
                 color: int = None,
                 thumbnail: EmbedThumbnail = None,
                 *args) -> None:
        self.type = type
        self.url = url
        self.title = title
        self.description = description
        self.color = color
        self.thumbnail = thumbnail


class Attachment:
    def __init__(self,
                 id: str = None,
                 filename: str = None,
                 size: int = None,
                 url: str = None,
                 proxy_url: str = None,
                 width: int = None,
                 height: int = None,
                 content_type: str = None,
                 *args) -> None:
        self.id = id
        self.filename = filename
        self.size = size
        self.url = url
        self.proxy_url = proxy_url
        self.width = width
        self.height = height
        self.content_type = content_type


class Message:
    def __init__(self,
                 id: str = None,
                 content: str = None,
                 channel_id: str = None,
                 author: ChannelUser = None,
                 attachments: list[discord.Attachment] = [],
                 embeds: list[discord.Embed] = [],
                 reactions: list[discord.Reaction] = [],
                 timestamp: str = None,
                 edited_timestamp: str = None,
                 **kwargs) -> None:
        self.id = id
        self.content = content
        self.channel_id = channel_id
        self.author = author
        self.attachments = attachments
        self.embeds = embeds
        self.reactions = reactions
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp


class FakeConnectionState:
    def __init__(self) -> None:
        self.http = None