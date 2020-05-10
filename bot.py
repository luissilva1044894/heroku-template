#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import environ
from traceback import TracebackException

import discord
from discord.ext.commands import Bot

bot = Bot(command_prefix='!', pm_help=False)

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

@bot.event
async def on_ready():
    print('=' * 75, end='\n\n')
    print(f'Logged in as: {bot.user.name} (ID:{bot.user.id}) | Connected to {len(bot.guilds)} servers | Connected to {len(set(bot.get_all_members()))} users')
    print(f'https://discordapp.com/oauth2/authorize?client_id={bot.user.name}&scope=bot&permissions=8')
    print(f'Successfully logged in and booted...!')
    print('=' * 75, end='\n\n')

    await bot.change_presence(activity=discord.Game(name='PyCharm'), status=discord.Status('dnd'))

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run(environ.get('DISCORD_BOT_TOKEN'))
