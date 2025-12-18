from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image
import io
import google.generativeai as genai
import json

# ==========================================
# あなたのAPIキー
GEMINI_API_KEY = "AIzaSyAPEBeTmDJcYC4_dTdNJ6IhO_4okARZJgM"
# ==========================================

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Auto-Select Server is running"}

@app.post("/process_image")
async def process_image(file: UploadFile = File(...)):
    # 1. 画像を読み込む
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    width, height = image.size
    print(f"画像受信: {width}x{height}")

    # ====================================================
    # ★ここが自動修復ポイント★
    # 使えるモデルを自動で検索してセットします
    target_model_name = "models/gemini-1.5-flash" # 第一希望
    
    try:
        available_models = []
        print("--- モデル探索開始 ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                print(f"発見: {m.name}")
        
        # もし第一希望がなければ、見つかったものの中から適当に選ぶ
        if target_model_name not in available_models:
            if "models/gemini-pro" in available_models:
                target_model_name = "models/gemini-pro"
            elif len(available_models) > 0:
                target_model_name = available_models[0]
            else:
                print("【致命的エラー】使えるモデルが1つもありません！")
        
        print(f"決定: {target_model_name} を使用します")
        model = genai.GenerativeModel(target_model_name)
        
    except Exception as e:
        print(f"モデル検索エラー: {e}")
        # 万が一検索に失敗したら強制的に指定
        model = genai.GenerativeModel("gemini-pro")
    # ====================================================

    # 2. Geminiへの命令
    prompt = """
    あなたはスマホ自動操作ロボットです。画像を見て、次にタップすべき場所の座標を教えてください。
    
    【今のミッション】
    「キャプチャを開始する」や「Start」、「停止」などのボタンを探して押してください。
    
    【回答ルール】
    必ず以下のJSON形式だけで答えてください。
    {"x": 500, "y": 1000}
    """

    try:
        # 3. 生成実行
        response = model.generate_content([prompt, image])
        text = response.text
        
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
        print(f"Gemini実行エラー: {e}")
        return {
            "action": "tap",
            "x": width // 2,
            "y": height // 2
        }