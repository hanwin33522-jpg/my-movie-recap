import os
import subprocess
import asyncio
import whisper
import edge_tts
from deep_translator import GoogleTranslator
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Edge TTS (Thiha Voice) အသုံးပြု၍ အသံဖိုင်ထုတ်ပေးသော function
async def generate_thiha_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process_movie', methods=['POST'])
def process_movie():
    data = request.json
    movie_url = data.get('url')

    if not movie_url:
        return jsonify({'error': 'Link ထည့်ပေးပါ။'}), 400

    try:
        raw_video = os.path.join(DOWNLOAD_FOLDER, 'raw_video.mp4')
        thiha_audio = os.path.join(DOWNLOAD_FOLDER, 'thiha_ai_voice.mp3')
        final_output = os.path.join(DOWNLOAD_FOLDER, 'final_dubbed_movie.mp4')

        # ဖိုင်အဟောင်းရှိရင် ဖျက်ပါ
        for f in [raw_video, thiha_audio, final_output]:
            if os.path.exists(f):
                os.remove(f)

        # ၁။ ဗီဒီယို ဒေါင်းလုဒ်ဆွဲခြင်း
        cmd_dl = f'yt-dlp -f "b[ext=mp4]/b" -o "{raw_video}" "{movie_url}"'
        subprocess.run(cmd_dl, shell=True, check=True)

        # ၂။ အသံကို စာသားပြောင်းခြင်း (Tiny Model)
        print("Loading Whisper Tiny Model for transcription...")
        model = whisper.load_model("tiny")
        result = model.transcribe(raw_video, fp16=False)
        english_text = result.get('text', '')

        if not english_text.strip():
            english_text = "Hello, welcome to this movie recap video."

        # ၃။ အင်္ဂလိပ်မှ မြန်မာစာသို့ ဘာသာပြန်ခြင်း
        myanmar_text = GoogleTranslator(source='auto', target='my').translate(english_text)

        # ၄။ AI ရဲ့ Thiha Voice ဖြင့် အသံဖိုင် ဖန်တီးခြင်း
        asyncio.run(generate_thiha_voice(myanmar_text, thiha_audio))

        # ၅။ RAM စားသက်သာစေရန် 480p Resolution သို့ လျော့ချ၍ ပေါင်းစပ်ခြင်း
        ffmpeg_cmd = (
            f'ffmpeg -y -i "{raw_video}" -i "{thiha_audio}" '
            f'-filter_complex "[0:v]hflip,scale=480:854:force_original_aspect_ratio=increase,crop=480:854[v];[1:a]atempo=1.03[a]" '
            f'-map "[v]" -map "[a]" -c:v libx264 -preset ultrafast -crf 28 -c:a aac "{final_output}"'
        )
        
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        recap_info = f"""
        <h3>🎬 AI Thiha အသံဖြင့် ပြန်ဆိုထားသော ဗီဒီယို ရပါပြီ!</h3>
        <hr>
        <p><b>📝 မူရင်း စာသား:</b> {english_text}</p>
        <p><b>🇲🇲 မြန်မာစာ ဘာသာပြန်:</b> {myanmar_text}</p>
        <p><b>🗣️ သုံးထားသော AI အသံ:</b> Microsoft Thiha Voice (my-MM-ThihaNeural)</p>
        <p><b>📐 Resolution:</b> 480p (RAM Optimized)</p>
        <p>အောက်ပါ ခလုတ်ကို နှိပ်၍ ဒေါင်းလုဒ်ဆွဲနိုင်ပါပြီ။</p>
        """

        return jsonify({
            'success': True,
            'recap': recap_info,
            'download_link': '/download'
        })

    except Exception as e:
        print("Error details:", str(e))
        return jsonify({'error': f'လုပ်ဆောင်စဉ် Error တက်သွားပါသည်: {str(e)}'}), 500

@app.route('/download')
def download_file():
    file_path = os.path.join(DOWNLOAD_FOLDER, 'final_dubbed_movie.mp4')
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name='thiha_ai_dubbed_480p.mp4')
    return "File မရှိပါ။", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
