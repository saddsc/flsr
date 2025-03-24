from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import asyncio
import os
import re

# 🔹 بيانات تسجيل الدخول (يفضل وضعها في متغيرات بيئية بدلاً من وضعها مباشرة في الكود)
API_ID = int(os.getenv("API_ID", 28058773))
API_HASH = os.getenv("API_HASH", "e9e57b0112979b26db98ed965b55ec23")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7561453887:AAEMHh30AV3MGw0sH9uS6sWyckmtiCc7Ues")
OWNER_ID = int(os.getenv("OWNER_ID", 908814910)) # يمكنك ضبط المالك في Render

# 🔹 إنشاء عميل Telethon
client = TelegramClient("bot_session", API_ID, API_HASH)

# 🔹 قائمة المشرفين
admins_file = "admins.txt"
if not os.path.exists(admins_file):
with open(admins_file, "w") as f:
f.write(str(OWNER_ID) + "\n")

def load_admins():
""" تحميل قائمة المشرفين من الملف """
with open(admins_file, "r") as f:
return {int(line.strip()) for line in f.readlines()}

def save_admin(admin_id):
""" إضافة مشرف جديد إلى الملف """
with open(admins_file, "a") as f:
f.write(str(admin_id) + "\n")

def remove_admin(admin_id):
""" إزالة مشرف من الملف """
admins = load_admins()
admins.discard(admin_id)
with open(admins_file, "w") as f:
for admin in admins:
f.write(str(admin) + "\n")

admins = load_admins()

# 🔹 استخراج معرف المجموعة من الرابط
group_link_pattern = re.compile(r"(?:https?://)?t\.me/([a-zA-Z0-9_]+)|(-100\d+)")

def extract_chat_id(message_text):
""" استخراج معرف المجموعة من الرابط """
match = group_link_pattern.search(message_text)
if match:
return f"@{match.group(1)}" if match.group(1) else int(match.group(2))
return None

@client.on(events.NewMessage())
async def handle_message(event):
""" التعامل مع الأوامر والرسائل """
sender = await event.get_sender()
sender_id = sender.id
message_text = event.message.text

# التحقق من الصلاحيات
if sender_id not in admins:
await event.respond("🚫 ليس لديك صلاحية لاستخدام هذا البوت!")
return

# 🔹 أمر رفع مشرف
if message_text.startswith("/رفع_مشرف"):
if sender_id != OWNER_ID:
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
except (IndexError, ValueError):
await event.respond("❌ استخدم الأمر بهذا الشكل: `/رفع_مشرف <ايدي_الشخص>`")
return

# 🔹 أمر حذف مشرف
if message_text.startswith("/حذف_مشرف"):
if sender_id != OWNER_ID:
await event.respond("🚫 هذا الأمر متاح فقط للمالك.")
return
try:
admin_id = int(message_text.split()[1])
if admin_id == OWNER_ID:
await event.respond("🚫 لا يمكنك إزالة المالك من المشرفين!")
return
if admin_id not in admins:
await event.respond("❌ هذا المستخدم ليس مشرفًا بالفعل.")
else:
remove_admin(admin_id)
admins.remove(admin_id)
await event.respond(f"✅ تم إزالة المشرف {admin_id}.")
except (IndexError, ValueError):
await event.respond("❌ استخدم الأمر بهذا الشكل: `/حذف_مشرف <ايدي_الشخص>`")
return

# 🔹 أمر عرض المشرفين
if message_text.startswith("/عرض_المشرفين"):
admin_list = "\n".join(map(str, admins))
await event.respond(f"📌 قائمة المشرفين:\n{admin_list}")
return

# 🔹 التحقق من معرف المجموعة
chat_id = extract_chat_id(message_text)
if not chat_id:
await event.respond("❌ أرسل رابط مجموعة صحيح مثل:\n🔹 `t.me/MyGroup`\n🔹 أو `-1001234567890`")
return

await event.respond("✅ جاري حظر الأعضاء بسرعة...")

offset = 0
limit = 200
all_users = []

# 🔹 جلب جميع الأعضاء
while True:
participants = await client(GetParticipantsRequest(
chat_id, ChannelParticipantsSearch(''), offset=offset, limit=limit, hash=0
))
if not participants.users:
break
all_users.extend(participants.users)
offset += len(participants.users)
await asyncio.sleep(0.1) # تجنب الحظر من تيليجرام

await event.respond(f"📌 إجمالي عدد الأعضاء: {len(all_users)}")

# 🔹 قائمة لحظر الأعضاء بسرعة
banned_users = []
failed_users = []

for i in range(0, len(all_users), 100):
tasks = []
batch = all_users[i:i+100]
for user in batch:
if not user.is_self:
tasks.append(client.kick_participant(chat_id, user.id))

results = await asyncio.gather(*tasks, return_exceptions=True)

for user, result in zip(batch, results):
if isinstance(result, Exception):
failed_users.append(f"{user.first_name} ({user.id}): {result}")
else:
banned_users.append(f"{user.first_name} ({user.id})")

# 🔹 إرسال تقرير نهائي
report = "✅ تم حظر جميع الأعضاء بنجاح!\n\n"
report += f"👥 عدد المحظورين: {len(banned_users)}\n"
if failed_users:
report += f"❌ لم يتم حظر بعض الأعضاء:\n" + "\n".join(failed_users)

await event.respond(report)

async def main():
""" تشغيل البوت على Render """
await client.connect()

# التأكد من تسجيل الدخول
if not await client.is_user_authorized():
await client.start(bot_token=BOT_TOKEN)

print("✅ البوت يعمل الآن...")
await client.run_until_disconnected()

with client:
client.loop.run_until_complete(main())
