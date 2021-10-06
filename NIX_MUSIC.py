import os
import asyncio
import functools
import itertools
import math
import random
import discord
import youtube_dl

from async_timeout import timeout
from discord.ext import commands, tasks
from api import Rank, Normal, ARAM

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''

Token = os.environ["Token"]

class VoiceError(Exception):
    pass

class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '{0.title}'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('일치하는 항목을 찾을 수 없어요. `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('일치하는 항목을 찾을 수 없어요. `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('일치하는 항목을 찾을 수 없어요. `{}`'.format(webpage_url))
        
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @classmethod
    async def search_source(self, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None, bot):
        self.bot = bot
        channel = ctx.channel
        loop = loop or asyncio.get_event_loop()

        self.search_query = '%s%s:%s' % ('ytsearch', 10, ''.join(search))

        partial = functools.partial(self.ytdl.extract_info, self.search_query, download=False, process=False)
        info = await loop.run_in_executor(None, partial)

        self.search = {}
        self.search["title"] = f'다음을 검색합니다:\n**{search}**'
        self.search["type"] = 'rich'
        self.search["color"] = 7506394
        self.search["author"] = {'name': f'{ctx.author.name}', 'url': f'{ctx.author.avatar_url}',
                                'icon_url': f'{ctx.author.avatar_url}'}

        lst = []
        count = 0
        e_list = []
        for e in info['entries']:
            # lst.append(f'`{info["entries"].index(e) + 1}.` {e.get("title")} **[{YTDLSource.parse_duration(int(e.get("duration")))}]**\n')
            VId = e.get('id')
            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
            lst.append(f'`{count + 1}.` [{e.get("title")}]({VUrl})\n')
            count += 1
            e_list.append(e)

        lst.append('\n**선택할 숫자를 입력하고 종료하려면 `취소` 또는 `종료`를 입력하십시오.**')
        self.search["description"] = "\n".join(lst)

        em = discord.Embed.from_dict(self.search)
        await ctx.send(embed=em, delete_after=45.0)

        def check(msg):
            return msg.content.isdigit() == True and msg.channel == channel or msg.content == '취소' or msg.content == '종료'

        try:
            m = await self.bot.wait_for('message', check=check, timeout=45.0)

        except asyncio.TimeoutError:
            rtrn = 'timeout'

        else:
            if m.content.isdigit() == True:
                sel = int(m.content)
                if 0 < sel <= 10:
                    for key, value in info.items():
                        if key == 'entries':
                            """data = value[sel - 1]"""
                            VId = e_list[sel-1]['id']
                            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
                            partial = functools.partial(self.ytdl.extract_info, VUrl, download=False)
                            data = await loop.run_in_executor(None, partial)
                    rtrn = self(ctx, discord.FFmpegPCMAudio(data['url'], **self.FFMPEG_OPTIONS), data=data)
                else:
                    rtrn = 'sel_invalid'
            elif m.content == '취소':
                rtrn = 'cancel'
            elif m.content == '종료':
                rtrn = 'cancel'
            else:
                rtrn = 'sel_invalid'

        return rtrn

    @staticmethod
    def parse_duration(duration: int):
        if duration > 0:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)

            duration = []
            if days > 0:
                duration.append('{}'.format(days))
            if hours > 0:
                duration.append('{}'.format(hours))
            if minutes > 0:
                duration.append('{}'.format(minutes))
            if seconds > 0:
                duration.append('{}'.format(seconds))
            
            value = ':'.join(duration)
            
            duration.append('분')
            value = ''.join(duration)
            
        elif duration == 0:
            value = "LIVE"
        
        return value


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester
    
    def create_embed(self):
        embed = (discord.Embed(title='현재 재생 중', description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.blurple())
                .add_field(name='길이', value=self.source.duration)
                .add_field(name='요청자', value=self.requester.mention)
                .add_field(name='업로더', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                .add_field(name='상세보기', value='[클릭]({0.source.url})'.format(self))
                .set_thumbnail(url=self.source.thumbnail)
                .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if self.loop == False:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
                
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())
            
            #If the song is looped
            elif self.loop == True:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
            
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('이 명령은 DM 채널에서 사용할 수 없어요.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('오류가 발생했습니다:\n{}'.format(str(error)))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != bot.user.id:
            print(f"{message.guild}/{message.channel}/{message.author.name}>{message.content}")
            if message.embeds:
                print(message.embeds[0].to_dict())

    @commands.command(name='입장', aliases=['join'], invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='호출', aliases=['summon'])
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """음성 채널로 봇을 호출합니다.
        채널이 지정되지 않은 경우 채널에 가입됩니다.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('음성 채널에 입장해주세요!')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='퇴장', aliases=['leave'])
    async def _leave(self, ctx: commands.Context):
        """대기열을 지우고 음성 채널을 종료합니다."""

        if not ctx.voice_state.voice:
            return await ctx.send('음성 채널에 입장해주세요!')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='볼륨', aliases=['volume', 'v'])
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """플레이어의 볼륨을 설정합니다."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('현재 재생 중인 항목이 없어요.')

        if 0 > volume > 100:
            return await ctx.send('볼륨은 0 ~ 100 사이여야 해요!')
        ctx.voice_client.source.volume = volume / 100
        await ctx.send('볼륨을 `{}%`로 조정했어요.'.format(ctx.voice_client.source.volume * 100))

    @commands.command(name='재생정보', aliases=['now', 'np'])
    async def _now(self, ctx: commands.Context):
        """현재 재생 중인 노래를 표시합니다."""
        embed = ctx.voice_state.current.create_embed()
        await ctx.send(embed=embed)

    @commands.command(name='일시정지', aliases=['pause'])
    async def _pause(self, ctx: commands.Context):
        """현재 재생 중인 노래를 일시 중지합니다."""
        print(">>>Pause Command:")
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='재개', aliases=['resume', 're', 'res'])
    async def _resume(self, ctx: commands.Context):
        """현재 일시 중지된 노래를 재개합니다."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='중지', aliases=['stop', 's'])
    async def _stop(self, ctx: commands.Context):
        """노래 재생을 중지하고 대기열을 지웁니다."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⛔')

    @commands.command(name='스킵', aliases=['skip', 'sk'])
    async def _skip(self, ctx: commands.Context):
        """노래 스킵 투표. 요청자는 자동으로 건너뛸 수 있습니다.
        이 노래를 건너뛰려면 3개의 스킵 투표가 필요합니다.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('재생 중인 노래가 없어요.')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('스킵을 하려면 최소 3명 이상의 투표가 필요해요. **{}/3**'.format(total_votes))

        else:
            await ctx.send('이미 투표 하셨어요.')

    @commands.command(name="대기열", aliases=['queue', 'q'])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """플레이어의 대기열을 표시합니다.
        선택적으로 표시할 페이지를 지정할 수 있습니다. 각 페이지에는 10개의 요소가 있습니다.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('대기열이 없습니다.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**트랙 {}**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name="셔플", aliases=['shuffle', 'sp'])
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('대기열이 없습니다.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='제거', aliases=['remove'])
    async def _remove(self, ctx: commands.Context, index: int):
        """대기열에서 지정된 인덱스의 노래를 제거합니다."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('대기열이 없습니다.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='반복재생', aliases=['loop'])
    async def _loop(self, ctx: commands.Context):
        """현재 재생 중인 곡을 루프합니다.
        이 명령을 다시 호출하여 노래를 풉니다.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('재생 중인 곡이 없습니다.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='재생', aliases=['play', 'p'])
    async def _play(self, ctx: commands.Context, *, search: str):
        """노래를 재생합니다.
        대기열에 노래가 있는 경우 다른 노래가 재생될 때까지 대기열에 있습니다.
        이 명령은 URL이 제공되지 않으면 다양한 사이트에서 자동으로 검색합니다.
        이 사이트들의 목록은 https://rg3.github.io/youtube-dl/supportedsites.html 에서 찾을 수 있습니다.
        """

        async with ctx.typing():
            try:
                source = await YTDLSource.search_source(ctx, search, loop=self.bot.loop, bot=self.bot)
            except YTDLError as e:
                await ctx.send('이 요청을 처리하는 동안 오류가 발생했습니다.: {}'.format(str(e)))
            else:
                if source == 'sel_invalid':
                    await ctx.send('잘못된 선택입니다.')
                elif source == 'cancel':
                    await ctx.send('👌')
                elif source == 'timeout':
                    await ctx.send(':alarm_clock: **시간이 초과되었어요.**')
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self._join)

                    song = Song(source)
                    await ctx.voice_state.songs.put(song)
                    await ctx.send('`{}` 노래를 지금 재생할게요!'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('음성 채널에 입장해주세요!')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('봇이 이미 음성 채널에 있습니다!')
    """
    @commands.command(name='mmr')
    async def _MMR(self, ctx: commands.Context, *, search: str):
        async with ctx.typing():
            _Rank = Rank(search)
            _Normal = Normal(search)
            _ARAM = ARAM(search)
            embed = (discord.Embed(title='소환사 정보', description='```css\n{}\n```'.format(search), color=discord.Color.blurple())
                .add_field(name='솔로랭크', value='```css\n{}\n```'.format(_Rank[0]), inline = False)
                .add_field(name='노말', value='```css\n{}\n```'.format(_Normal[0]), inline = False)
                .add_field(name='무작위 총력전', value='```css\n{}\n```'.format(_ARAM[0]), inline = False)
                .set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url))
            await ctx.send(embed=embed)
    """         
bot = commands.Bot(command_prefix='!', case_insensitive=True)
bot.add_cog(Music(bot))
status = itertools.cycle(['Produced By JeongYun','Playing Music'])

@tasks.loop(seconds=3)
async def change_status():
    await bot.change_presence(status = discord.Status.online, activity = discord.Game(next(status)))

@bot.event
async def on_ready():
    change_status.start()
    print('클라이언트로 로그인했습니다:\n{0.user.name}\n{0.user.id}'.format(bot))
    
@bot.command(name='서버종료', aliases=['server_stop'])
@commands.is_owner()
async def botstop(ctx):
    print('Goodbye')
    await ctx.send('봇 서버가 종료 됩니다.')
    await bot.logout()
    return

bot.run(Token)
