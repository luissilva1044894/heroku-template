
import discord
from discord.ext import commands

import asyncio
import itertools
import sys
import traceback
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL


#flat-playlist:True?
#extract_flat:True
youtube_dl_options = {
  'format': 'bestaudio/best',
  'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',#'{}'
  'restrictfilenames': True,
  'noplaylist': True,
  'nocheckcertificate': True,
  'ignoreerrors': True,
  'logtostderr': False,
  'quiet': True,
  'no_warnings': True,
  'default_search': 'auto',
  'source_address': '0.0.0.0', # ipv6 addresses cause issues sometimes

  'extractaudio':True,
  'audioformat':'opus',
}

stim = {
  'default_search': 'auto',
  'ignoreerrors':True,
  'quiet': True,
  'no_warnings': True,
  'simulate': True, # do not keep the video files
  'nooverwrites': True,
  'keepvideo': False,
  'noplaylist': True,
  'skip_download': False,
  'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
  'before_options': '-nostdin',#-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5
  'options': '-vn'
}

ytdl = YoutubeDL(youtube_dl_options)

class VoiceConnectionError(commands.CommandError):
  """Custom Exception class for connection errors."""

class InvalidVoiceChannel(VoiceConnectionError):
  """Exception for cases of invalid Voice Channels."""

class YTDLSource(discord.PCMVolumeTransformer):
  def __init__(self, source, *, data, requester, volume=0.5):
    super().__init__(source, volume)
    self.requester = requester

    self.title = data.get('title')
    self.web_url = data.get('webpage_url')

    self.data = data
    self.url = data.get('url')
    self.thumbnail = data.get('thumbnail')
    self.duration = data.get('duration')
    self.views = data.get('view_count')
    self.playlist = {}

    # YTDL info dicts (data) have other useful information you might want
    # https://github.com/rg3/youtube-dl/blob/master/README.md

  def __getitem__(self, item: str):
    """Allows us to access attributes similar to a dict.

    This is only useful when you are NOT downloading."""
    return self.__getattribute__(item)

  @classmethod
  async def video_url(cls, url, ytdl, *, loop=None, stream=False):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
    data1 = {'queue':[]}
    if 'entries' in data:
      if len(data['entries']) > 1:
        playlist_titles = [title['title'] for title in data['entries']]
        data1 = {'title':data['title'], 'queue':playlist_titles}
        data1['queue'].pop(0)

      data = data['entries'][0]

    filename = data['url'] if stream else ytdl.prepare_filename(data)
    return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data), data1

  async def get_info(self,url):
    yt = youtube_dl.YoutubeDL(stim)
    down = yt.extract_info(url,download=False)
    data1 = {'queue':[]}
    if 'entries' in down:
      if len(down['entries']) > 1:
        playlist_titles = [title['title'] for title in down['entries']]
        data1 = {'title':down['title'], 'queue':playlist_titles}

      down = down['entries'][0]['title']    
    return down, data1

  @classmethod
  async def create_source(cls, ctx, search: str, *, loop, download=False):
    loop = loop or asyncio.get_event_loop()

    data = await loop.run_in_executor(None, partial(ytdl.extract_info, url=search, download=download))

    if 'entries' in data:
      # take first item from a playlist
      data = data['entries']
      if data and isinstance(data, (tuple, list)) and len(data) > 0:
        data = data[0]

    await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```', delete_after=15)

    if not download:
      return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}
    return cls(discord.FFmpegPCMAudio(ytdl.prepare_filename(data)), data=data, requester=ctx.author)

  @classmethod
  async def regather_stream(cls, data, *, loop):
    """Used for preparing a stream, instead of downloading.

    Since Youtube Streaming links expire."""
    loop = loop or asyncio.get_event_loop()
    requester = data['requester']

    data = await loop.run_in_executor(None, partial(ytdl.extract_info, url=data['webpage_url'], download=False))

    return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)

class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.

    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.

    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300): # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            self.np = await self._channel.send(f'**Now Playing:** `{source.title}` requested by '
                                               f'`{source.requester}`')
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        if guild.voice_client and hasattr(guild.voice_client, 'disconnect'):
            await guild.voice_client.disconnect()

        # Hi, what about cleaning the ffmpeg process when calling the cleanup fonct?
        try:
            for s in self.players[guild.id].queue._queue:
                s.cleanup()
        except KeyError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        if isinstance(error, InvalidVoiceChannel):
            return await ctx.send('Error connecting to Voice Channel. Please make sure you are in a valid channel or provide me with one')

        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connect', aliases=['join'])
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        """Connect to voice.

        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.

        This command also handles moving the bot to different channels.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')

        await ctx.send(f'Connected to: **{channel}**', delete_after=20)

    @commands.command(name='play', aliases=['sing'])
    async def play_(self, ctx, *, search: str):
        """Request a song and add it to the queue.

        This command attempts to join a valid voice channel if the bot is not already in one.
        Uses YTDL to automatically search and retrieve a song.

        Parameters
        ------------
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

        await player.queue.put(source)

    @commands.command(name='pause')
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing() or vc.is_paused():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused the song!')

    @commands.command(name='resume')
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected() or not vc.is_paused():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed the song!')

    @commands.command(name='skip')
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected() or vc.is_paused() or not vc.is_playing():
            return await ctx.send('I am not currently playing anything!', delete_after=20)

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: Skipped the song!')

    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('There are currently no more queued songs.')

        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)}', description=fmt)

        await ctx.send(embed=embed)

    @commands.command(name='now_playing', aliases=['np', 'current', 'currentsong', 'playing'])
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('I am not currently playing anything!')

        try:
            # Remove our previous now_playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass

        player.np = await ctx.send(f'**Now Playing:** `{vc.source.title}` requested by `{vc.source.requester}`')

    @commands.command(name='volume', aliases=['vol'])
    async def change_volume(self, ctx, *, vol: float):
        """Change the player volume.

        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        if not 0 < vol < 201:
            return await ctx.send('Please enter a value between 1 and 200.')

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{vol}%**')

    @commands.command(name='stop')
    async def stop_(self, ctx):
        """Stop the currently playing song and destroy the player.

        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)

        await self.cleanup(ctx.guild)


def setup(bot):
    bot.add_cog(Music(bot))
