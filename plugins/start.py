from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
import json, string, random
import os
from plugins import constant
from datetime import datetime
from plugins.db_wrapper import DB

step = {
    'sp': 2,
    'start': 0
}

PATH = constant.PATH
txt = constant.TEXT
data = constant.DATA



def start_acc(_, client: Client, message: Message):
    if step['start'] == 1:
        return True


start_accept = filters.create(start_acc)


def join_check(_, client: Client, message: Message):
    data2 = json.loads(open(PATH + '/database.json', encoding='utf-8').read())
    joinButton = InlineKeyboardMarkup([
        [InlineKeyboardButton("عضویت در چنل ما", url=f"https://t.me/{data2['sponser'][1:]}")],
    ]
    )
    try:
        status = client.get_chat_member(chat_id=data2['sponser'], user_id=message.from_user.id)
        return True

    except UserNotParticipant:
        message.reply_text(
            f"سلام به ربات یوتیوب دانلود خوشومدی😎❤\n\n برای استفاده از امکانات ربات حتما باید تو چنل ما جوین باشی"
            , reply_markup=joinButton)

        return False


join = filters.create(join_check)


def get_random_string():
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(7))
    return result_str


@Client.on_message(filters.command("start") & join, group=-2)
def start(client: Client, message: Message):
    check_user = DB().check_user_register(message.from_user.id)
    if check_user:
        message.reply_text(txt['start_text'])
        step['start'] = 1
    else:
        now = datetime.now()
        # data['users'][str(message.from_user.id)] = {
        #     'user_last_download': str(now)
        # }
        DB().register_user(message.from_user.id, now)

        # with open(PATH + '/database.json', "w") as outfile:
        #     json.dump(data, outfile, indent=4)

        message.reply_text(txt['start_text'])
        step['start'] = 1
