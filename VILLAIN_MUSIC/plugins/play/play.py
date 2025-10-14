import random
import string
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from VILLAIN_MUSIC import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from VILLAIN_MUSIC.core.call import VILLAIN
from VILLAIN_MUSIC.utils import seconds_to_min
from VILLAIN_MUSIC.utils.decorators.play import PlayWrapper
from VILLAIN_MUSIC.utils.inline import botplaylist_markup
from VILLAIN_MUSIC.utils.logger import play_logs
from VILLAIN_MUSIC.utils.stream.stream import stream
from config import BANNED_USERS


@app.on_message(
    filters.command(
        [
            "play",
            "vplay",
            "cplay",
            "cvplay",
            "playforce",
            "vplayforce",
            "cplayforce",
            "cvplayforce",
        ],
        prefixes=["/", "!", "."],
    )
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(client, message: Message, _, chat_id, video, channel, playmode, url, fplay):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # 🧠 FIX 1: Handle reply messages (Voice / Audio / YouTube links etc.)
    if message.reply_to_message:
        rmsg = message.reply_to_message

        # 🎵 Voice / Audio handling (fixed NameError)
        if rmsg.audio or rmsg.voice:
            audio_file = rmsg.audio or rmsg.voice
            name = getattr(audio_file, "file_name", None) or getattr(audio_file, "file_unique_id", "voice_note")

            if audio_file.file_size > 104857600:
                return await mystic.edit_text(_["play_5"])

            duration_min = seconds_to_min(audio_file.duration)
            if audio_file.duration > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                )

            file_path = await Telegram.get_filepath(audio=audio_file)
            if await Telegram.download(_, message, mystic, file_path):
                message_link = await Telegram.get_link(message)
                dur = await Telegram.get_duration(audio_file, file_path)
                details = {
                    "title": name,
                    "link": message_link,
                    "path": file_path,
                    "dur": dur,
                }
                try:
                    await stream(
                        _,
                        mystic,
                        user_id,
                        details,
                        chat_id,
                        user_name,
                        message.chat.id,
                        streamtype="telegram",
                        forceplay=fplay,
                    )
                except Exception as e:
                    ex_type = type(e).__name__
                    err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                    return await mystic.edit_text(err)
                return await mystic.delete()
            return

        # 🎬 Video / Document handling
        elif rmsg.video or rmsg.document:
            video_file = rmsg.video or rmsg.document
            try:
                ext = video_file.file_name.split(".")[-1]
                if ext.lower() not in ["mp4", "mkv", "mov", "webm"]:
                    return await mystic.edit_text(
                        _["play_7"].format("mp4 | mkv | mov | webm")
                    )
            except:
                return await mystic.edit_text(
                    _["play_7"].format("mp4 | mkv | mov | webm")
                )

            if video_file.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
                return await mystic.edit_text(_["play_8"])

            file_path = await Telegram.get_filepath(video=video_file)
            if await Telegram.download(_, message, mystic, file_path):
                message_link = await Telegram.get_link(message)
                file_name = getattr(video_file, "file_name", "telegram_video")
                dur = await Telegram.get_duration(video_file, file_path)
                details = {
                    "title": file_name,
                    "link": message_link,
                    "path": file_path,
                    "dur": dur,
                }
                try:
                    await stream(
                        _,
                        mystic,
                        user_id,
                        details,
                        chat_id,
                        user_name,
                        message.chat.id,
                        video=True,
                        streamtype="telegram",
                        forceplay=fplay,
                    )
                except Exception as e:
                    ex_type = type(e).__name__
                    err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                    return await mystic.edit_text(err)
                return await mystic.delete()
            return

        # 🎧 YouTube link or caption reply fix
        if rmsg.text or rmsg.caption:
            query = rmsg.text or rmsg.caption
            try:
                details, track_id = await YouTube.track(query.strip())
            except:
                return await mystic.edit_text(_["play_3"])

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=video,
                    streamtype="youtube",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            await mystic.delete()
            return

    # 🧠 FIX 2: Direct /play <query> or /play <YouTube URL>
    if len(message.command) > 1:
        query = message.text.split(None, 1)[1].strip()
    elif url:
        query = url.strip()
    else:
        buttons = botplaylist_markup(_)
        return await mystic.edit_text(
            _["play_18"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    if "-v" in query:
        query = query.replace("-v", "")

    try:
        details, track_id = await YouTube.track(query)
    except:
        return await mystic.edit_text(_["play_3"])

    try:
        await stream(
            _,
            mystic,
            user_id,
            details,
            chat_id,
            user_name,
            message.chat.id,
            video=video,
            streamtype="youtube",
            forceplay=fplay,
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
        return await mystic.edit_text(err)

    await mystic.delete()
    await play_logs(message, streamtype="youtube")
