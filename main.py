from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from PIL import Image
import io

app = FastAPI()

class Command(BaseModel):
    action: str  # "tap" or "wait"
    x: int
    y: int

@app.get("/")
def read_root():
    return {"status": "Server is running"}

@app.post("/process_image")
async def process_image(file: UploadFile = File(...)):
    # 1. スマホから送られてきた画像を読み込む
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    width, height = image.size
    print(f"画像を受信しました！ サイズ: {width}x{height}")

    # 2. ここにAIの判断が入ります（今回はテスト用に「真ん中をタップ」と返します）
    center_x = width // 2
    center_y = height // 2

    print(f"命令: ({center_x}, {center_y}) をタップします")

    # 3. スマホに命令を返す
    return {
        "action": "tap",
        "x": center_x,
        "y": center_y
    }