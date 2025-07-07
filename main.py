import yfinance as yf
import asyncio
import datetime
import os
import subprocess
from edge_tts import Communicate
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
import urllib.request
import tarfile
import warnings

warnings.filterwarnings("ignore")

USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
TARGET_PATH = "ivr2:/7/"
FFMPEG_PATH = "./bin/ffmpeg"

def ensure_ffmpeg():
    if not os.path.exists(FFMPEG_PATH):
        print("⬇️ מוריד ffmpeg...")
        os.makedirs("bin", exist_ok=True)
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = "bin/ffmpeg.tar.xz"
        extract_path = "bin"
        urllib.request.urlretrieve(url, archive_path)
        with tarfile.open(archive_path) as tar:
            tar.extractall(path=extract_path)
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file == "ffmpeg":
                    os.rename(os.path.join(root, file), FFMPEG_PATH)
                    os.chmod(FFMPEG_PATH, 0o755)
                    break

def split_price(value):
    shekels = int(value)
    agorot = int(round((value - shekels) * 100))
    return shekels, agorot

def build_text():
    ticker = yf.Ticker("USDILS=X")
    data = ticker.history(period="1d", interval="1m")

    if data.empty:
        return None

    last_price = round(data["Close"].iloc[-1], 4)
    open_price = round(data["Open"].iloc[0], 4)
    high_price = round(data["High"].max(), 4)
    low_price = round(data["Low"].min(), 4)

    change = round(((last_price - open_price) / open_price) * 100, 2)
    change_type = "עלייה" if change >= 0 else "ירידה"
    change = abs(change)

    ps, pa = split_price(last_price)
    ls, la = split_price(low_price)
    hs, ha = split_price(high_price)

    text = f"שער הדולר היציג המעודכן עומד כעת על {ps} שקלים ו{pa} אגורות, " \
           f"מתחילת היום נרשמה {change_type} של {change} אחוז, " \
           f"ביממה האחרונה הדולר נע בטווח של {ls} שקלים ו{la} אגורות עד {hs} שקלים ו{ha} אגורות."
    
    print("📜 טקסט שנוצר:", text)
    return text

async def text_to_speech(text, filename):
    communicate = Communicate(text, voice="he-IL-AvriNeural")
    await communicate.save(filename)

def convert_to_wav(mp3_file, wav_file):
    ensure_ffmpeg()
    with open(os.devnull, 'w') as devnull:
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", mp3_file, "-ar", "8000", "-ac", "1", "-acodec", "pcm_s16le", wav_file],
            stdout=devnull,
            stderr=devnull
        )

def upload_to_yemot(wav_file, path):
    m = MultipartEncoder(fields={
        'token': TOKEN,
        'path': path + "001.wav",
        'file': ("001.wav", open(wav_file, 'rb'), 'audio/wav')
    })
    r = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=m, headers={'Content-Type': m.content_type})
    if r.ok:
        print("✅ הועלה בהצלחה")
    else:
        print("❌ שגיאה בהעלאה:", r.text)

async def main():
    print("🚀 ריצה התחילה...")
    text = build_text()
    if not text:
        print("⚠️ לא נמצאו נתונים")
        return

    await text_to_speech(text, "dollar.mp3")
    convert_to_wav("dollar.mp3", "dollar.wav")
    upload_to_yemot("dollar.wav", TARGET_PATH)

if __name__ == "__main__":
    asyncio.run(main())
