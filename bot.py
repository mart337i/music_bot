import lightbulb
import hikari
import lavaplayer
import logging
import os
import asyncio

SLASH_COMMAND = True  # if you want to use slash command, set True
PREFIX = "="  # prefix for commands
TOKEN = "OTA1MDUxMzg1NzA2NDY3MzI4.G7Hcm7.lbLXDG9WxdQ2p3l40fKosEb9Nl0VdnOvgG-iqk"  # token for bot
DEFAULT_ENABLED_GUILDS = []  # list of guilds that the bot will create slash commands for (if you want to use slash command)
# you can keep empty list if you don't want to use guild slash command it create globally for all guilds


# create a hikari client to get a events
bot = lightbulb.BotApp(
    "OTA1MDUxMzg1NzA2NDY3MzI4.G7Hcm7.lbLXDG9WxdQ2p3l40fKosEb9Nl0VdnOvgG-iqk",
    logs={
        "version": 1,
        "incremental": True,
        "loggers": {
            "hikari": {"level": "INFO"},
            "hikari.ratelimits": {"level": "TRACE_HIKARI"},
            "lightbulb": {"level": "DEBUG"},
        },
    },
    )

# create a lavaplayer client
lavalink = lavaplayer.LavalinkClient(
    host="127.0.0.1",  # your lavalink host
    port=8888,  # your lavalink port
    password="youshallnotpass",  # your lavalink password
    user_id=123  # your bot id
)

@bot.listen(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent):
    lavalink.set_user_id(bot.get_me().id)
    lavalink.set_event_loop(asyncio.get_event_loop())
    lavalink.connect()

# On voice state update the bot will update the lavalink node
@bot.listen(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent):
    await lavalink.raw_voice_state_update(event.guild_id, event.state.user_id, event.state.session_id, event.state.channel_id)

@bot.listen(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent):
    await lavalink.raw_voice_server_update(event.guild_id, event.endpoint, event.token)

implements = [lightbulb.commands.PrefixCommand] if not SLASH_COMMAND else [lightbulb.commands.PrefixCommand, lightbulb.commands.SlashCommand]

# Commands
# ------------------------------------- #
@bot.command()
@lightbulb.command(name="join", description="join voice channel")
@lightbulb.implements(*implements)
async def join_command(ctx: lightbulb.context.Context):
    voice_state = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id)
    if not voice_state:
        await ctx.respond("you are not in a voice channel")
        return
    channel_id = voice_state.channel_id
    await bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
    await lavalink.wait_for_connection(ctx.guild_id)
    await ctx.respond(f"join to <#{channel_id}>")

@bot.command()
@lightbulb.option(name="query", description="query to search", required=True)
@lightbulb.command(name="play", description="Play command", aliases=["p"])
@lightbulb.implements(*implements)
async def play_command(ctx: lightbulb.context.Context):
    query = ctx.options.query  # get query from options
    result = await lavalink.auto_search_tracks(query)  # search for the query
    if not ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id):
        await ctx.respond("you are not in a voice channel")
        return

    voice_state = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id)
    user_channel = ctx.get_channel()

    # Check if both are in the same channel
    if user_channel and voice_state and voice_state.channel_id != user_channel:
        voice_state =  ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id)
        channel_id = voice_state.channel_id
        await bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
        await lavalink.wait_for_connection(ctx.guild_id)
    if not result:
        await ctx.respond("not found result for your query")
        return
    elif isinstance(result, lavaplayer.TrackLoadFailed):
        await ctx.respond("Track load failed, try again later.\n```{}```".format(result.message))
        return
    elif isinstance(result, lavaplayer.PlayList):
        await lavalink.add_to_queue(ctx.guild_id, result.tracks, ctx.author.id)
        await ctx.respond(f"added {len(result.tracks)} tracks to queue")
        return 

    await lavalink.play(ctx.guild_id, result[0], ctx.author.id)  # play the first result
    await ctx.respond(f"[{result[0].title}]({result[0].uri})")  # send the embed

@bot.command()
@lightbulb.command(name="stop", description="Stop command")
@lightbulb.implements(*implements)
async def stop_command(ctx: lightbulb.context.Context):
    await lavalink.stop(ctx.guild_id)
    await ctx.respond("done stop the music")

@bot.command()
@lightbulb.command(name="skip", description="skip command", aliases=["s"])
@lightbulb.implements(*implements)
async def skip_command(ctx: lightbulb.context.Context):
    await lavalink.skip(ctx.guild_id)
    await ctx.respond("skipped ")

@bot.command()
@lightbulb.command(name="pause", description="Pause command")
@lightbulb.implements(*implements)
async def pause_command(ctx: lightbulb.context.Context):
    await lavalink.pause(ctx.guild_id, True)
    await ctx.respond("The music is paused now")

@bot.command()
@lightbulb.command(name="resume", description="Resume command")
@lightbulb.implements(*implements)
async def resume_command(ctx: lightbulb.context.Context):
    await lavalink.pause(ctx.guild_id, False)
    await ctx.respond("The music is resumed now")

@bot.command()
@lightbulb.option(name="position", description="Position to seek", required=True)
@lightbulb.command(name="seek", description="Seek command")
@lightbulb.implements(*implements)
async def seek_command(ctx: lightbulb.context.Context):
    position = ctx.options.position
    await lavalink.seek(ctx.guild_id, position)
    await ctx.respond(f"done seek to {position}")

@bot.command()
@lightbulb.option(name="vol", description="Volume to set", required=True)
@lightbulb.command(name="volume", description="Volume command")
@lightbulb.implements(*implements)
async def volume_command(ctx: lightbulb.context.Context):
    volume = ctx.options.vol
    await lavalink.volume(ctx.guild_id, volume)
    await ctx.respond(f"done set volume to {volume}%")


@bot.command()
@lightbulb.command(name="queue", description="Queue command")
@lightbulb.implements(*implements)
async def queue_command(ctx: lightbulb.context.Context):
    node = await lavalink.get_guild_node(ctx.guild_id)
    embed = hikari.Embed(
        description="\n".join(
            [f"{n+1}- [{i.title}]({i.uri})" for n, i in enumerate(node.queue)])
    )
    await ctx.respond(embed=embed)

@bot.command()
@lightbulb.command(name="np", description="Now playing command")
@lightbulb.implements(*implements)
async def np_command(ctx: lightbulb.context.Context):
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node or not node.queue:
        await ctx.respond("nothing playing")
        return
    await ctx.respond(f"[{node.queue[0].title}]({node.queue[0].uri})")

@bot.command()
@lightbulb.command(name="repeat", description="Repeat command")
@lightbulb.implements(*implements)
async def repeat_command(ctx: lightbulb.context.Context):
    node = await lavalink.get_guild_node(ctx.guild_id)
    stats = False if node.repeat else True
    await lavalink.repeat(ctx.guild_id, stats)
    if stats:
        await ctx.respond("done repeat the music")
        return
    await ctx.respond("done stop repeat the music")

@bot.command()
@lightbulb.command(name="shuffle", description="Shuffle command")
@lightbulb.implements(*implements)
async def shuffle_command(ctx: lightbulb.context.Context):
    await lavalink.shuffle(ctx.guild_id)
    await ctx.respond("done shuffle the music")

@bot.command()
@lightbulb.command(name="leave", description="Leave command")
@lightbulb.implements(*implements)
async def leave_command(ctx: lightbulb.context.Context):
    await bot.update_voice_state(ctx.guild_id, None)
    await ctx.respond("done leave the voice channel")
# ------------------------------------- #

@lavalink.listen(lavaplayer.TrackStartEvent)
async def track_start_event(event: lavaplayer.TrackStartEvent):
    logging.info(f"start track: {event.track.title}")

@lavalink.listen(lavaplayer.TrackEndEvent)
async def track_end_event(event: lavaplayer.TrackEndEvent):
    logging.info(f"track end: {event.track.title}")

@lavalink.listen(lavaplayer.WebSocketClosedEvent)
async def web_socket_closed_event(event: lavaplayer.WebSocketClosedEvent):
    logging.error(f"error with websocket {event.reason}")



bot.run()
