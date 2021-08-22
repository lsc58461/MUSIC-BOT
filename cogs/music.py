from os import name
import time
import discord
from discord.ext import commands
from bot import MusicBot
from . import *

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot: MusicBot = bot

    def cog_check(self, ctx):
        return (
            is_connected(ctx)
            and ctx.guild is not None
            and is_on_same_voice_channel(ctx)
        )

    @commands.command(name="입장")
    async def join(self, ctx):
        await ctx.author.voice.channel.connect()
        self.bot.loop.create_task(
            ctx.guild.change_voice_state(
                channel=ctx.channel, self_mute=False, self_deaf=True
            )
        )
        await ctx.reply(f"`{ctx.voice_client.channel}`채널에 입장했어요.")

    @commands.command(name="재생", aliases=["p"])
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def play(self, ctx, *, query):
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
            self.bot.loop.create_task(
                ctx.guild.change_voice_state(
                    channel=ctx.channel, self_mute=False, self_deaf=True
                )
            )
        await self.bot.play_music(ctx, query)

    @commands.command(name="중지", aliases=["s"])
    @commands.check(is_playing)
    async def stop(self, ctx):
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.message.add_reaction("⛔")

    @commands.command(name="볼륨", aliases=["v"])
    @commands.check(is_playing)
    async def volume(self, ctx, volume: int = None):
        if not volume:
            return await ctx.reply(f"현재 볼륨: `{ctx.voice_client.source.volume * 100}%`")
        ctx.voice_client.source.volume = volume / 100
        self.bot.players[ctx.guild.id]["volume"] = ctx.voice_client.source.volume
        await ctx.reply(
            f"볼륨을 `{ctx.voice_client.source.volume * 100}%`로 조정했어요.",
        )

    @commands.command(name="스킵", aliases=["sk"])
    @commands.check(is_playing)
    async def skip(self, ctx):
        ctx.voice_client.stop()
        await ctx.message.add_reaction("👌")

    @commands.command(name="nowplaying", aliases=("np",))
    @commands.check(is_playing)
    async def nowplaying(self, ctx):
        embed = discord.Embed(
            title="현재 재생 중",
            description=f"[{self.bot.players[ctx.guild.id]['current']['data']['info']['title']}](https://youtu.be/{self.bot.players[ctx.guild.id]['current']['data']['info']['id']})"
            f"\n{make_progress_bar(time.time() - self.bot.players[ctx.guild.id]['current']['started'], self.bot.players[ctx.guild.id]['current']['data']['info']['duration'])}\n"
            f"{duration_format(time.time() - self.bot.players[ctx.guild.id]['current']['started'], self.bot.players[ctx.guild.id]['current']['data']['info']['duration'])}",
        )
        await ctx.reply(
            embed=embed,
        )

    @commands.command(name="일시정지", aliases=["q"])
    @commands.check(is_playing)
    async def queue(self, ctx):
        embed = discord.Embed(
            title="대기열",
            description="\n".join(
                [
                    f"{i + 1}. "
                    + self.bot.players[ctx.guild.id]["queue"][i]["info"]["title"]
                    for i in range(len(self.bot.players[ctx.guild.id]["queue"]))
                ]
            ),
        )  # for i in range(len(queue))
        await ctx.reply(
            embed=embed,
        )

    @commands.command(name="삭제")
    @commands.check(is_playing)
    async def remove(self, ctx, index: int):
        try:
            del self.bot.players[ctx.guild.id]["queue"][index + 1]
        except IndexError:
            return await ctx.reply(
                "올바른 숫자를 써주세요.",
            )
        await ctx.reply(f"대기열에서 {index}번째 노래를 삭제했습니다.")


def setup(bot):
    bot.add_cog(Music(bot))
