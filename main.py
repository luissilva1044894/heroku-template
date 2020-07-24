#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from os import environ
import traceback

from twitchio import Context
from twitchio.ext import commands

try:
  from dotenv import load_dotenv
except ImportError:
  pass
else:
  load_dotenv()
finally:
  client_id = environ.get('TWITCH_CLIENT_ID')
  initial_channels = str(environ.get('TWITCH_INICIAL_CHANNELS') or '').split(',')
  initial_extensions=['basic']
  irc_token = environ.get('TWITCH_IRC_TOKEN')
  nick = environ.get('TWITCH_NICK')
  prefix = environ.get('TWITCH_BOT_PREFIX') or '!'
  if nick not in initial_channels:
    initial_channels.append(nick)

class Bot(commands.Bot):
  def __init__(self, nick, irc_token, client_id=None, prefix=None, initial_channels=[], initial_extensions=[]):
    super().__init__(client_id=client_id, initial_channels=initial_channels, irc_token=irc_token, nick=nick, prefix=prefix)

    for ext in initial_extensions:
      try:
        if not str(ext).lower().startswith('cogs'):
          ext = f'cogs.{ext}'
        self.load_module(ext)
      except Exception as e:
        print(f'Failed to load extension {ext}.')
        traceback.print_exc()

  async def event_ready(self):
    """Called once when the bot goes online."""
    print(f'Ready | {self.nick}')

  async def event_command_error(self, ctx, error):
    print(f'Error running command: {error} for {ctx.message.author.name}')

  async def event_message(self, msg):
    """Runs every time a message is sent in chat."""
    print(msg.content)
    if msg.author.name.casefold() != self.nick.casefold():
      ctx = await self.get_context(msg, cls=Context)
      return await self.handle_commands(msg, ctx=ctx)

if __name__ == '__main__':
  bot = Bot(nick=nick,
    irc_token=irc_token,
    client_id=client_id,
    initial_channels=initial_channels,
    prefix=prefix,
    initial_extensions=initial_extensions,
  )
  bot.run()
