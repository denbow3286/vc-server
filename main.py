from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image
import io
import google.generativeai as genai
import json

# ==========================================
# あなたのGemini APIキー
GEMINI_API_KEY = "AIzaSyAPEBeTmDJcYC4_dTdNJ6IhO_4okARZJgM" 
# ==========================================

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Gemini Server is running"}

@app.post("/process_image")
async def process_image(file: UploadFile = File(...)):
    # 1. 画像を読み込む
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    width, height = image.size
    print(f"画像受信: {width}x{height}")

    # 2. Geminiへの命令（プロンプト）
    prompt = """
    あなたはスマホ自動操作ロボットです。画像を見て、次にタップすべき場所の座標を教えてください。
    
    【今のミッション】
    「キャプチャを開始する」や「Start」のような、録画や開始に関連するボタンを探して押してください。
    もしボタンが見当たらなければ、画面の中央を指定してください。

    【回答ルール】
    必ず以下のJSON形式だけで答えてください。説明は一切不要です。
    {"x": 500, "y": 1000}
    
    ※座標は画像のピクセル値で答えてください。
    """

    try:
        # 3. Geminiに画像を見せて判断させる
        response = model.generate_content([prompt, image])
        text = response.text
        
        # 4. JSONを綺麗に取り出す
        clean_text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        target_x = data.get("x", width // 2)
        target_y = data.get("y", height // 2)

        print(f"Geminiの指令: ({target_x}, {target_y}) をタップせよ")

        return {
            "action": "tap",
            "x": target_x,
            "y": target_y
        }

    except Exception as e:
        print(f"Geminiエラー: {e}")
        # エラー時は画面中央をタップ
        return {
            "action": "tap",
            "x": width // 2,
            "y": height // 2
        }