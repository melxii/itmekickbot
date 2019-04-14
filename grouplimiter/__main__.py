from . import bot, db, bot_py


if __name__ == "__main__":
    db.connect()
    db.create_table(
        "data",
        "chat_id integer primary key, mem_limit integer",
        check_first=True)
    bot.run_until_disconnected()
