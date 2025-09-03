#translator.py

from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, DRAMA_TITLE

client = OpenAI(api_key=OPENAI_API_KEY)

# 中国語字幕を日本語に翻訳する関数
def translate_chinese_to_ja(text: str) -> str:
    if not text:
        return ""# 空文字なら空
    try:
        messages = [
            {"role": "system", "content": f"あなたはプロの翻訳者です。自然で流暢な日本語訳を提供してください。これは「{DRAMA_TITLE}」という中国ドラマの字幕です。翻訳した文章のみを出力し、句読点や記号は出力しないでください。"},
            {"role": "user", "content": text}
        ]
        # ChatGPT API翻訳
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3
        )
        # 翻訳文のみ
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[翻訳エラー]: {e}")
        return "(翻訳失敗)"
