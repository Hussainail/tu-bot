import os
import telebot
import google.generativeai as genai
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap
import tempfile

BOT_TOKEN = "8757571553:AAFMbfrVqyUi4BaqY-X92WSD5LicuZzT_Qw"
GEMINI_API_KEY = "AIzaSyBSBlZ3-wiZQX-4bkb8pxciMbHuGTBnLzs"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "🌿 أهلاً بك في بوت تصميم القصائد\n\nأرسل لي بيت شعر وسأكمل القصيدة وأصنع لك فيديو جميل 🎬")

@bot.message_handler(func=lambda m: m.text not in ['30 ثانية', '1 دقيقة', '2 دقيقة'])
def handle_poem(message):
    chat_id = message.chat.id
    text = message.text
    user_data[chat_id] = {'verse': text}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('30 ثانية', '1 دقيقة', '2 دقيقة')
    bot.send_message(chat_id, f"📜 استلمت البيت:\n_{text}_\n\nاختر طول الفيديو:", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ['30 ثانية', '1 دقيقة', '2 دقيقة'])
def handle_duration(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "أرسل بيت الشعر أولاً")
        return
    durations = {'30 ثانية': 30, '1 دقيقة': 60, '2 دقيقة': 120}
    duration = durations[message.text]
    verse = user_data[chat_id]['verse']
    bot.send_message(chat_id, "⏳ جاري إنشاء القصيدة والفيديو...")
    num_verses = max(3, duration // 10)
    response = model.generate_content(
        f"أكمل هذه القصيدة الحسينية بأسلوب عراقي عاطفي. البيت الأول: {verse}\nاكتب {num_verses} أبيات فقط، كل بيت في سطر منفصل، بدون ترقيم."
    )
    full_poem = verse + "\n" + response.text
    verses = [v.strip() for v in full_poem.split('\n') if v.strip()]
    clips = []
    verse_duration = duration / len(verses[:num_verses])
    for v in verses[:num_verses]:
        img = create_verse_image(v)
        clip = ImageClip(img).set_duration(verse_duration)
        clips.append(clip)
    final = concatenate_videoclips(clips, method="compose")
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        output_path = f.name
    final.write_videofile(output_path, fps=24, codec='libx264', audio=False)
    with open(output_path, 'rb') as video:
        bot.send_video(chat_id, video, caption=f"🌿 {verse}")
    os.unlink(output_path)
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "أرسل بيتاً جديداً 🎬", reply_markup=markup)

def create_verse_image(verse):
    img = Image.new('RGB', (1080, 1920), color=(20, 40, 20))
    draw = ImageDraw.Draw(img)
    for y in range(1920):
        alpha = y / 1920
        r = int(10 + alpha * 30)
        g = int(30 + alpha * 60)
        b = int(10 + alpha * 40)
        draw.line([(0, y), (1080, y)], fill=(r, g, b))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
    except:
        font = ImageFont.load_default()
    lines = textwrap.wrap(verse, width=20)
    y_start = 900 - (len(lines) * 80) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (1080 - w) // 2
        draw.text((x+2, y_start+2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y_start), line, font=font, fill=(255, 220, 150))
        y_start += 90
    return img

bot.polling()
