from . import bot, db
import asyncio
from telethon import events
from telethon.tl.functions.channels import (EditBannedRequest,
                                            GetParticipantRequest)
from telethon.tl.types import (ChannelParticipantAdmin, ChannelParticipantCreator, ChatBannedRights)
import datetime


@bot.on(events.NewMessage(incoming=True, pattern=r"\/start"))
async def start(event):
    await event.reply("Hi there! My name is Group Limiter and if you can't figure it out from the name, I'm here to help you limit the members of your groups.\n\n"
                      "Usage: \n  Type `/setlimit (number)` to set the members limit for this group. When someone joins I will kick him if the members count exceedes the members limit!\n"
                      "   Type `/remlimit` to remove the members limit from your group\n"
                      "   Type `/getlimit` to get the members limit for this group")


@bot.on(events.NewMessage(incoming=True, pattern=r"^\/setlimit (\d*)", func=lambda e: not e.is_private))
async def set_limit(event):
    if not (await event.get_chat()).admin_rights:
        await event.reply("I wish I could help you with that but I need admin rights to limit the members of this group")
        return
    if not isinstance((await bot(GetParticipantRequest(event.chat_id, event.sender_id))).participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
        await event.reply("Nice Try! Only the group admin or creator can change the memebr limit for this group.")
        return

    limit = event.pattern_match.group(1)
    mem_count = (await bot.get_participants(event.chat_id)).total
    db.insert("data", "chat_id, mem_limit", ("?,?"), args=(event.chat_id, limit), replace=True)

    if int(mem_count) > int(limit):
        await event.reply(f"The members count is higher than the limit you've set. I will still kick everyone that joins the group if the members count isn't lower than the set limit!")
        return

    await event.reply(f"Member limit for this group has been set to {limit}. I will still kick everyone that joins the group if the members count isn't lower than the set limit!")


@bot.on(events.NewMessage(incoming=True, pattern=r"^\/remlimit", func=lambda e: not e.is_private))
async def rem_limit(event):
    if not isinstance((await bot(GetParticipantRequest(event.chat_id, event.sender_id))).participant, (ChannelParticipantCreator, ChannelParticipantAdmin)):
        await event.reply("Nice Try! Only the group admin or creator can change the memebr limit for this group.")
        return
    db.delete("data", "chat_id = ?", args=(event.chat_id,))
    await event.reply("Removed the member limit for this group!")


@bot.on(events.NewMessage(incoming=True, pattern=r"^\/getlimit", func=lambda e: not e.is_private))
async def get_limit(event):
    limit = db.select("mem_limit", "data", where="chat_id = ?", args=(event.chat_id,), limit=0)
    if limit:
        await event.reply(f"This group has a limit of {limit[0][0]} members!!")
    else:
        await event.reply(f"This group has no member limit set!!")


@bot.on(events.ChatAction(func=lambda e: e.user_added or e.user_joined))
async def kick_user(event):

    limit = db.select("mem_limit", "data", where="chat_id = ?", args=(event.chat_id), limit=0)

    if limit:
        if (await bot.get_participants(event.chat_id)).total >= int(limit[0]):
            await event.reply(f"This group has a limit of {limit[0]} members. You will be kicked in 5 seconds")
            await asyncio.sleep(5)
            try:
                await bot(EditBannedRequest(event.chat_id, (await event.get_input_user()).user_id, ChatBannedRights(until_date=datetime.timedelta(minutes=1), view_messages=True)))
            except Exception as exc:
                await event.reply(f"Failed to kick the user due `{str(exc)}`")
