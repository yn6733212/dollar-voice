import os
import subprocess
import datetime
import pytz
import asyncio
import yfinance as yf
from edge_tts import Communicate
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import tarfile
import urllib.request

# === פרטי התחברות לימות המשיח ===
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
UPLOAD_PATH = "ivr2:/6"

# === נתונים: שליפת שער הדולר מ־Yahoo Finance ===
ticker = yf.Ticker("USDILS=X")
data = ticker.history(period="1d", interval="1m")

last_price = round(data["Close"][-1], 4)
open_price = round(data["Open"][0], 4)
high_price = round(data["High"].max(), 4)
low_price = round(data["Low"].min(), 4)

change = round(((last_price - open_price) / open_price) * 100, 2)
change_type = "עלייה" if change >= 0 else "ירידה"
change = abs(change)

def split_price(value):
    shekels = int(value)
    agorot = int(round((value - shekels) * 100))
    return shekels, agorot

ps, pa = split_price(last_price)
ls, la = split_price(low_price)
hs, ha = split_price(high_price)

# שעה ותאריך נוכחיים
tz = pytz.timezone("Asia/Jerusalem")
now = datetime.datetime.now(tz)
datetime_prefix = now.strftime("%d_%m_%H_%M")

# טקסט להקראה
text = f"שער הדולר היציג המעודכן עומד כעת על {ps} שקלים ו{pa} אגורות, " \
       f"מתחילת היום נרשמה {change_type} של {change} אחוז, " \
       f"ביממה האחרונה הדולר נע בטווח של {ls} שקלים ו{la} אגורות עד {hs} שקלים ו{ha} אגורות."

print("🎙️ טקסט להקראה:", text)

# === שמות קבצים ===
TEMP_MP3 = "temp.mp3"
WAV_FILE = "001.wav"

# === בדיקה והתקנת ffmpeg אם צריך ===
def ensure_ffmpeg():
    if not os.path.exists("ffmpeg_bin"):
        print("⬇️ מתקין ffmpeg...")
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        urllib.request.urlretrieve(url, "ffmpeg.zip")
        os.system("unzip -o ffmpeg.zip -d ffmpeg_bin")
        for root, dirs, files in os.walk("ffmpeg_bin"):
            for name in files:
                if name == "ffmpeg.exe":
                    os.rename(os.path.join(root, name), "ffmpeg.exe")
                    break
        print("✅ ffmpeg הותקן.")
    else:
        print("🎯 ffmpeg כבר קיים.")

ensure_ffmpeg()

# === יצירת קובץ שמע באמצעות edge-tts ===
async def generate_audio():
    communicate = Communicate(text=text, voice="he-IL-AvriNeural")
    await communicate.save(TEMP_MP3)

asyncio.run(generate_audio())

# === המרה ל-WAV בפורמט תואם ימות המשיח ===
subprocess.run([
    "ffmpeg", "-y",
    "-i", TEMP_MP3,
    "-ar", "8000",
    "-ac", "1",
    "-acodec", "pcm_s16le",
    WAV_FILE
])

print("✅ קובץ WAV נוצר:", WAV_FILE)

# === העלאה לימות המשיח ===
with open(WAV_FILE, "rb") as f:
    m = MultipartEncoder(
        fields={
            "token": TOKEN,
            "path": f"{UPLOAD_PATH}/{WAV_FILE}",
            "file": ("file", f, "audio/wav")
        }
    )
    response = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=m, headers={"Content-Type": m.content_type})

if response.ok:
    print("📤 קובץ הועלה לשלוחה 6 בהצלחה.")
else:
    print("❌ שגיאה בהעלאה:", response.text)
