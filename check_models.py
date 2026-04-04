import google.generativeai as genai
import os
from dotenv import load_dotenv

# 載入你的 API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("🔍 正在查詢您的 API Key 支援的模型清單...\n")

# 列出所有支援生成內容的模型
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 可用模型名稱: {m.name}")
    print("\n🎉 查詢完成！")
except Exception as e:
    print(f"❌ 查詢失敗，錯誤訊息：{e}")
    