def is_connected(ctx):
    if ctx.author.voice:
        return True
    else:
        ctx.bot.loop.create_task(ctx.reply("음성 채널에 입장해주세요!", mention_author=False))
        return False


def is_on_same_voice_channel(ctx):
    if is_connected(ctx) and ctx.voice_client:
        return ctx.author.voice.channel == ctx.voice_client.channel
    elif is_connected(ctx) and not ctx.voice_client:
        return True


def is_playing(ctx):
    return ctx.voice_client.is_playing()


def make_progress_bar(value, total):
    position_front = round(value / total * 16)
    position_back = 16 - position_front

    return "▬" * position_front + "🔘" + "▬" * position_back


def duration_format(now, duration):
    now, duration = round(now), round(duration)
    nminute, nsecond = divmod(now, 60)
    nhour, nminute = divmod(nminute, 60)
    now = (
        f"{str(nhour) + '시간 ' if nhour else ''}"
        f"{str(nminute) + '분 '}"
        f"{str(nsecond) + '초 '}"
    )
    dminute, dsecond = divmod(duration, 60)
    dhour, dminute = divmod(dminute, 60)
    duration = (
        f"{str(dhour) + '시간 ' if nhour else ''}"
        f"{str(dminute) + '분 '}"
        f"{str(dsecond) + '초 '}"
    )
    return f"{now} / {duration}"
