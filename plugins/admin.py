import time
import asyncio

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json, os
from pyrogram import filters, Client
import re
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import FloodWait
import sys, requests
import instaloader
from instaloader import InstaloaderException
from plugins import constant
from plugins.db_wrapper import DB
from utils.server_stats import ServerStats

PATH = constant.PATH
txt = constant.TEXT
data = constant.DATA

ADMIN = [170256094, 79049016, 703859331]

admin_step = {
    'sp': 2
}

insta = {'level': 0, 'id': "default", 'pass': "defult"}


def admin_inline_maker() -> list:
    return [
        [
            InlineKeyboardButton(txt['status'], callback_data='st'),
            InlineKeyboardButton(txt['sponser'], callback_data='sp'),
            InlineKeyboardButton(txt['globalpm'], callback_data='sg')
        ],

        [
            InlineKeyboardButton(txt['shutdown'], callback_data='sh'),
            InlineKeyboardButton("📊 آمار سرور", callback_data='server_stats')
        ],

        [
            InlineKeyboardButton(txt['add_acc'], callback_data='si'),

        ],

        [
            InlineKeyboardButton("Send Special Post 🚀", callback_data='sendspcpost'),

        ],

    ]


@Client.on_message(filters.command('panel') & filters.user(ADMIN))
async def admin_panel(_: Client, message: Message):
    print("admin panel")
    admin_step['sp'] = 2
    await message.reply_text("Admin Panel",
                       reply_markup=InlineKeyboardMarkup(
                           admin_inline_maker()
                       )
                       )


async def set_sp_custom(_, __, message: Message):
    if admin_step['sp'] == 1:
        if re.findall("^@", message.text):
            return True
        else:
            await message.reply_text("فرمت وارد شده غلط است")
            return False
    else:
        return False


sp_filter = filters.create(set_sp_custom)


async def admin_panel_custom(_, __, query):
    return re.findall(r"^[s|h|l]", query.data)


static_data_filter = filters.create(admin_panel_custom)


def user_counter():
    users = DB().get_users_id()
    return len(users)


@Client.on_callback_query(static_data_filter)
async def answer(_, callback_query: CallbackQuery):
    data = json.loads(open(PATH + '/database.json', encoding='utf-8').read())

    if callback_query.data == 'server_stats':
        # Show loading message
        await callback_query.edit_message_text("در حال دریافت آمار سرور...")
        
        # Get server stats
        stats = await ServerStats.get_server_stats()
        message = await ServerStats.format_server_stats_message(stats)
        
        # Show stats with back button
        await callback_query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
            ])
        )
        return
    
    elif callback_query.data == 'back_to_admin':
        await callback_query.edit_message_text(
            "Admin Panel",
            reply_markup=InlineKeyboardMarkup(admin_inline_maker())
        )
        return
    
    elif callback_query.data == 'sendspcpost':
        await callback_query.edit_message_text("پست مورد نظر را جهت ارسال به کانال ارسال کنید")
        admin_step['sp'] = 11

    if callback_query.data == 'likeit' and f"@{callback_query.message.chat.username}".lower() == data['sponser'].lower():
        DB().update_last_like(callback_query.from_user.id, time.time())
        addlike = DB().add_like(callback_query.message.id, callback_query.from_user.id, data['sponser'])
        getlikes = DB().get_likes(callback_query.message.id, data['sponser'])
        await callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{getlikes[0]} 👍", callback_data='likeit'),
                    InlineKeyboardButton(f"{getlikes[1]} 👎", callback_data='hateit')
                ],
            ])
        )

    elif callback_query.data == 'hateit' and f"@{callback_query.message.chat.username}".lower() == data['sponser'].lower():
        DB().update_last_like(callback_query.from_user.id, time.time())
        addlike = DB().add_unlike(callback_query.message.id, callback_query.from_user.id, data['sponser'])
        getlikes = DB().get_likes(callback_query.message.id, data['sponser'])
        await callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{getlikes[0]} 👍", callback_data='likeit'),
                    InlineKeyboardButton(f"{getlikes[1]} 👎", callback_data='hateit')
                ],
            ])
        )
    
    elif callback_query.data == 'st':
        # Show loading message
        await callback_query.edit_message_text("در حال دریافت آمار...")
        
        # Get server stats
        stats = await ServerStats.get_server_stats()
        server_stats = await ServerStats.format_server_stats_message(stats, short_format=True)
        
        # Show combined stats
        await callback_query.edit_message_text(
            f"📊 آمار کلی\n\n👥 تعداد کاربران: {user_counter()}\n🔗 اسپانسر: {data['sponser']}\n🚀 تاریخ راه‌اندازی: 2021/23/10\n\n📡 آمار سرور:\n{server_stats}"
        )

    elif callback_query.data == 'sp':
        await callback_query.edit_message_text(
            "ابتدا ربات را در چنل مورد نظر ادمین کن سپس آیدی ربات رو برام بفرست\n فرمت صحیح ==> @RemGanG"
        )
        admin_step['sp'] = 1

    elif callback_query.data == 'sg':
        await callback_query.edit_message_text(
            "یه پیام برای بات ارسال کن و روش /send_to_all رو ریپلای کن !"
        )

    elif callback_query.data == 'sh':
        sys.exit()

    elif callback_query.data == 'si':
        callback_query.edit_message_text("آیدی اکانتی که میخواهید اضافه شود رو وارد کنید")
        insta['level'] = 1


@Client.on_message(filters.command('send_to_all') & filters.user(ADMIN))
async def send_to_all(client: Client, message: Message) -> None:
    if message.reply_to_message:
        all_users = DB().get_users_id()
        count = 0
        await message.reply_text(f'Sending to {len(all_users)} users... ')
        for user in all_users:
            try:
                await client.send_message(user[0], message.reply_to_message.text)
                count += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                print("Failed to send message to all users: {}".format(e))
                pass
        await message.reply_text(f'Sent to {count} of {len(all_users)}')
    else:
        await message.reply_text('You have to reply on a message')


@Client.on_message(sp_filter)
async def set_sp(_: Client, message: Message):
    data['sponser'] = message.text
    with open(PATH + '/database.json', "w") as outfile:
        json.dump(data, outfile, indent=4)
        await message.reply_text("اسپانسر بات با موفقیت تغییر کرد ✅")
    admin_step['sp'] = 0


@Client.on_message(filters.user(ADMIN))
def getpost(_, message: Message) -> None:

    if message.text != None and message.text.lower() == '/panel':
        return

    elif admin_step['sp'] == 11:
        
        aa=requests.get(f"https://talro.ir/Like.php?type=copyMessage&chat={data['sponser']}&fromchat={message.from_user.id}&msg={message.id}").json()
        print(aa)
        DB().register_post(aa['result']['message_id'], data['sponser'])
        message.reply_text("با موفقیت ارسال شد", reply_markup=InlineKeyboardMarkup(
            admin_inline_maker()
        ))
        admin_step['sp'] = 2

@Client.on_message(filters.text & filters.user(ADMIN), group=3)
def set_insta_acc(_, message: Message) -> None:

    if insta['level'] == 1:
        insta['id'] = message.text
        message.reply_text("رمز خود را وارد کنید")
        insta['level'] = 2

    elif insta['level'] == 2:
        insta['pass'] = message.text
        insta['level'] = 3

        L = instaloader.Instaloader()
        try:
            L.login(insta['id'], insta['pass'])
            L.save_session_to_file()
            message.reply_text("این اکانت به لیست اکانت ها اضافه شد ! =)")

            # instagram_data['users'][insta['id']] = {
            #     'id': insta['id'],
            #     'password': insta['pass']
            # }
            DB().save_insta_acc(insta['id'], insta['pass'])

            # with open(PATH + '/instagram_acc.json', "w") as outfile:
            #     json.dump(instagram_data, outfile, indent=4)

        except InstaloaderException as e:
            strr = str(e)
            if "Checkpoint required. Point your browser to" in strr:
                clean_url = strr.replace("Login: Checkpoint required. Point your browser to ", '').replace(' - follow the instructions, then retry.', '')
                requests.get(clean_url)
                time.sleep(3)
                insta['level'] = 2
                set_insta_acc(_, message)
            else:
                print(e)
                message.reply_text("موفق به اضافه کردن این اکانت نشدم !")
                insta['level'] = 0
