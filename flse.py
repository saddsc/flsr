from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsBanned, InputPeerChannel
import asyncio
import re
import os

# ✅ بيانات الاتصال
api_id = 28058773  
api_hash = "e9e57b0112979b26db98ed965b55ec23"
bot_token = "7561453887:AAEMHh30AV3MGw0sH9uS6sWyckmtiCc7Ues"
owner_id = 908814910  

# ✅ إنشاء عميل Telethon
client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=bot_token)

# ✅ إعدادات المشرفين
admins_file = "admins.txt"

if not os.path.exists(admins_file):
    with open(admins_file, "w") as f:
        f.write(str(owner_id) + "\n")  

def load_admins():
    """ تحميل قائمة المشرفين من الملف """
    with open(admins_file, "r") as f:
        return {int(line.strip()) for line in f.readlines() if line.strip().isdigit()}

def save_admin(admin_id):
    """ إضافة مشرف جديد """
    with open(admins_file, "a") as f:
        f.write(str(admin_id) + "\n")

def remove_admin(admin_id):
    """ حذف مشرف """
    admins = load_admins()
    admins.discard(admin_id)
    with open(admins_file, "w") as f:
        for admin in admins:
            f.write(str(admin) + "\n")

admins = load_admins()

# ✅ استخراج معرف المجموعة
group_link_pattern = re.compile(r"(?:https?://)?t\.me/([a-zA-Z0-9_]+)|(-100\d+)")

def extract_chat_id(message_text):
    match = group_link_pattern.search(message_text)
    if match:
        return f"@{match.group(1)}" if match.group(1) else int(match.group(2))
    return None

@client.on(events.NewMessage())
async def handle_message(event):
    sender = await event.get_sender()
    sender_id = sender.id
    message_text = event.message.text

    if sender_id not in admins:
        await event.respond("🚫 ليس لديك صلاحية لاستخدام هذا البوت!\n🔹 فقط المشرفين يمكنهم استخدامه.")
        return

    if message_text.startswith("/رفع_مشرف"):
        if sender_id != owner_id:
            await event.respond("🚫 هذا الأمر متاح فقط للمالك.")
            return
        try:
            new_admin_id = int(message_text.split()[1])
            if new_admin_id in admins:
                await event.respond("✅ هذا المستخدم مشرف بالفعل.")
            else:
                save_admin(new_admin_id)
                admins.add(new_admin_id)
                await event.respond(f"✅ تم ترقية المستخدم {new_admin_id} إلى مشرف.")
        except:
            await event.respond("❌ يرجى استخدام الأمر كالتالي: `/رفع_مشرف <ايدي_الشخص>`")
        return

    if message_text.startswith("/حذف_مشرف"):
        if sender_id != owner_id:
            await event.respond("🚫 هذا الأمر متاح فقط للمالك.")
            return
        try:
            admin_id = int(message_text.split()[1])
            if admin_id == owner_id:
                await event.respond("🚫 لا يمكنك إزالة المالك!")
                return
            if admin_id not in admins:
                await event.respond("❌ هذا المستخدم ليس مشرفًا.")
            else:
                remove_admin(admin_id)
                admins.remove(admin_id)
                await event.respond(f"✅ تم إزالة المشرف {admin_id}.")
        except:
            await event.respond("❌ يرجى استخدام الأمر كالتالي: `/حذف_مشرف <ايدي_الشخص>`")
        return

    if message_text.startswith("/عرض_المشرفين"):
        admin_list = "\n".join(map(str, admins))
        await event.respond(f"📌 قائمة المشرفين:\n{admin_list}")
        return

    chat_id = extract_chat_id(message_text)
    if not chat_id:
        await event.respond("❌ يرجى إرسال رابط مجموعة صحيح.")
        return

    await event.respond("✅ جاري حظر الأعضاء...")

    try:
        entity = await client.get_entity(chat_id)
        if not isinstance(entity, InputPeerChannel):
            await event.respond("❌ لم يتم العثور على المجموعة.")
            return

        offset = 0
        limit = 200
        total_banned = 0

        while True:
            participants = await client(GetParticipantsRequest(
                entity, ChannelParticipantsSearch(''), offset, limit, hash=0
            ))

            if not participants.users:
                break

            tasks = []
            for user in participants.users:
                tasks.append(client.edit_permissions(entity, user.id, view_messages=False))
                total_banned += 1

            await asyncio.gather(*tasks)
            offset += len(participants.users)

        await event.respond(f"✅ تم حظر {total_banned} عضوًا من المجموعة.")
    except Exception as e:
        await event.respond(f"❌ حدث خطأ أثناء الحظر: {e}")

# ✅ تشغيل البوت
print("✅ البوت يعمل بنجاح!")
client.run_until_disconnected()
