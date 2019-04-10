
# MIT License

# Copyright (c) 2019 Nitan Alexandru Marcel

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import asyncio
import datetime
import logging
import os
import sqlite3


from telethon import TelegramClient, events
from telethon.tl.functions.channels import (EditBannedRequest,
                                            GetParticipantRequest)
from telethon.tl.types import (ChannelParticipantAdmin,
                               ChannelParticipantCreator, ChatBannedRights)

logging.basicConfig(level=logging.INFO)

try:
    API_ID = os.environ["APP_ID"]
    API_HASH = os.environ["APP_HASH"]
    TOKEN = os.environ["TOKEN"]
except KeyError as e:
    quit(e.args[0] + ' missing from environment variables')

bot = TelegramClient("grouplimiterbot", API_ID, API_HASH)

bot.start(bot_token=TOKEN)


def execute(query, fetch=False):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    res = cur.execute(query)
    conn.commit()
    if fetch is True:
        try:
            return res.fetchone()
        finally:
            conn.close()
    else:
        conn.close()


execute(query=('''CREATE TABLE IF NOT EXISTS data (
                                        chat_id integer primary key,
                                        mem_limit integer
                                        )'''))


@bot.on(events.NewMessage(incoming=True, pattern=r"\/start"))
async def start(event):
    await event.reply("Hi there! My name is Group Limiter and if you can't figure it out from the name I'm here to help you limit the members of this group.\n\n"
                      "Usage: \n  Type `/setlimit (number)` to set the memebers limit for this group. When someone joins I will kick him if the members count exceedes the memebr limit!\n"
                      "   Type `/remlimit` to remove the member limit from your group\n"
                      "   Type `/getlimit` to get the member limit for this group")


@bot.on(events.NewMessage(incoming=True, pattern=r"^\/setlimit (\d*)"))
async def set_limit(event):
    if not (await event.get_chat()).admin_rights:
        await event.reply("I wish I could help you with that but I need admin rights to limit the members of this group")
        return
    if not isinstance((await bot(GetParticipantRequest(event.chat_id, event.sender_id))).participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
        await event.reply("Nice Try! Only the group admin or creator can change the memebr limit for this group.")
        return

    limit = event.pattern_match.group(1)
    mem_count = (await bot.get_participants(event.chat_id)).total
    execute(
        (f'''INSERT OR REPLACE INTO data VALUES ({event.chat_id}, {limit})'''))

    if int(mem_count) > int(limit):
        await event.reply(f"The members count is higher than the limit you've set. I will still kick everyone that joins the group if the members count isn't lower than the set limit!")
        return

    await event.reply(f"Member limit for this group has been set to {limit}. I will still kick everyone that joins the group if the members count isn't lower than the set limit!")


@bot.on(events.NewMessage(incoming=True, pattern=r"^\/remlimit"))
async def rem_limit(event):
    if not isinstance((await bot(GetParticipantRequest(event.chat_id, event.sender_id))).participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
        await event.reply("Nice Try! Only the group admin or creator can change the memebr limit for this group.")
        return
    execute(
        (f'''DELETE FROM data WHERE chat_id = {event.chat_id}'''),
        fetch=False)
    await event.reply("Removed the member limit for this group!")


@bot.on(events.NewMessage(incoming=True, pattern=r"^\/getlimit"))
async def get_limit(event):
    limit = execute(
        (f'''SELECT mem_limit FROM data WHERE chat_id =  {event.chat_id}'''),
        fetch=True)
    if limit:
        await event.reply(f"This group has a limit of {limit[0]} members!!")
    else:
        await event.reply(f"This group has no member limit set!!")


@bot.on(events.ChatAction(func=lambda e: e.user_added or e.user_joined))
async def kick_user(event):
    limit = execute(
        (f'''SELECT mem_limit FROM data WHERE chat_id =  {event.chat_id}'''),
        fetch=True)

    if limit:
        if (await bot.get_participants(event.chat_id)).total >= int(limit[0]):
            await event.reply(f"This group has a limit of {limit[0]} members. You will be kicked in 5 seconds")
            await asyncio.sleep(5)
            try:
                await bot(EditBannedRequest(event.chat_id, (await event.get_input_user()).user_id, ChatBannedRights(until_date=datetime.timedelta(minutes=1), view_messages=True)))
            except Exception as exc:
                await event.reply(f"Failed to kick the user due `{str(exc)}`")

if __name__ == "__main__":
    bot.run_until_disconnected()
