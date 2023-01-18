import qrcode
import asyncio
from remoteauthclient import RemoteAuthClient
from remoteauthclient.remoteauthclient import User


async def start_auth_generation(on_fingerprint, on_token, on_user, on_cancel=None):
    client = RemoteAuthClient()

    @client.event('on_fingerprint')
    async def _on_fingerprint(data):
        if asyncio.iscoroutinefunction(on_fingerprint):
            await on_fingerprint(data)
        else:
            on_fingerprint(data)

    @client.event('on_token')
    async def _on_token(token):
        if asyncio.iscoroutinefunction(on_token):
            await on_token(token)
        else:
            on_token(token)

    @client.event('on_userdata')
    async def _on_user(user: User):
        if asyncio.iscoroutinefunction(on_user):
            await on_user(user)
        else:
            on_user(user)

    @client.event('on_cancel')
    async def _on_cancel():
        if not on_cancel:
            return
            
        if asyncio.iscoroutinefunction(on_cancel):
            await on_cancel()
        else:
            on_cancel()

    await client.run()

if __name__ == '__main__':
    def on_fingerprint(data):
        print(f'Got auth link: {data}')

        image = qrcode.make(data)
        image.save('auth_qr.png')

    def on_token(token):
        print(f'Got token: {token}')

    def on_user(user: User):
        print(f'User is attempting to login: {user.getName()}')

    def _on_cancel():
        print(f'User cancelled auth')

    asyncio.run(start_auth_generation(
        on_fingerprint=on_fingerprint,
        on_token=on_token,
        on_user=on_user,
        on_cancel=_on_cancel
    ))
