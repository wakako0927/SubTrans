<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
</head>
<body>

<header>
  <h1>中国語字幕翻訳システム</h1>
  <p class="muted">
    本プログラムは、中国語の映像に含まれる字幕を検出・翻訳し、<br>
    日本語訳を動画と同期して表示する Python アプリケーションです。<br>
    Flask単体で 非同期ジョブ管理・進捗可視化・同期ハイライトUI を実現しています。
  </p>
</header>

<section>
  <h2>特徴</h2>
  <ul>
    <li><strong>字幕検出:</strong> 字幕領域の検出精度を上げるためにファインチューニングした YOLOv8 のモデルを構築</li>
    <li><strong>文字認識:</strong> EasyOCR（中国語簡体）を使用。他のOCRも切り替え可能なインタフェースを設計</li>
    <li><strong>翻訳:</strong> OpenAI API による日本語翻訳</li>
    <li><strong>重複除外:</strong> 文字の誤認識を抑制するために、NFKC正規化＋編集距離＋2-gram Jaccard のハイブリッド判定を実装</li>
    <li><strong>非同期処理 & 進捗バー:</strong> Flaskスレッドで OCR→翻訳 を処理し、/status API で進捗をポーリング</li>
    <li><strong>同期表示UI:</strong> 左に動画・右に字幕。動画の再生位置に応じて字幕がハイライトされ、自動でスクロールします</li>
  </ul>
</section>

<section>
  <h2>ディレクトリ構成</h2>
  <pre><code>SubTrans
├─ app.py                 # Flaskアプリ本体（非同期ジョブ/進捗API/メモリ保持）
├─ config.py              # 設定（フレーム間隔など）
├─ duplicate_filter.py    # 重複除外ロジック
├─ ocr_processor.py       # OCR（YOLO + EasyOCR）
├─ translator.py          # 翻訳処理（OpenAI API）
├─ models/
│  └─ best.pt            # 自作YOLOモデル（約6MB）
├─ templates/
│  ├─ upload.html        # アップロード画面
│  ├─ progress.html      # 解析中画面
│  └─ lyric.html         # 結果ビュー
└─ static/
   └─ css/
      └─ main.css        # 共通スタイル
</code></pre>
</section>

<section>
  <h2>セットアップ</h2>

  <h3>1) 環境</h3>
  <ul>
    <li>Python 3.10–3.12</li>
    <li>Windows / Linux（GPUは環境依存）</li>
  </ul>

  <h3>2) 依存関係</h3>
  <pre><code>pip install opencv-python numpy easyocr ultralytics openai torch torchvision torchaudio flask</code></pre>
  <p class="note">PyTorch は公式ガイドに従ってインストールしてください。</p>

  <h3>3) OpenAI API キー</h3>
  <pre><code># PowerShell
setx OPENAI_API_KEY "sk-xxxx"</code></pre>

  <h3>4) 設定ファイル例（config.py）</h3>
  <pre><code>OPENAI_MODEL   = "gpt-4o"
FRAME_INTERVAL = 5
MODEL_PATH     = "models/best.pt"</code></pre>
</section>

<section>
  <h2>使い方</h2>
  <h3>Webアプリ（Flask）</h3>
  <pre><code>python app.py
# ブラウザで http://127.0.0.1:5000</code></pre>

  <ol>
    <li>アップロードページで動画を選択</li>
    <li>解析中ページで進捗を確認</li>
    <li>結果ページで動画と同期字幕を表示</li>
  </ol>
  <h4>出力例</h4>
    <p><img src="https://raw.githubusercontent.com/wakako0927/subtrans/refs/heads/main/SubTrans/images/sumple_image.JPEG" alt="例" width="700"></p>
</code></pre>
</section>

<section>
  <h2>モデル（YOLOv8）について</h2>
  <p><code>models/best.pt</code>（約6MB）を同梱しています。</p>

  <h3>学習データ</h3>
  <ul>
    <li>中国ドラマのスクリーンショットを自作収集</li>
    <li>クラス: subtitle のみ</li>
    <li>train 400 / val 70</li>
  </ul>

  <h3>学習条件</h3>
  <ul>
    <li>モデル: YOLOv8n</li>
    <li>画像サイズ: 640x640</li>
    <li>バッチサイズ: 16</li>
    <li>エポック: 約100</li>
  </ul>
</section>

<section>
  <h2>内部実装のポイント</h2>
  <ul>
    <li>OCR直後に重複除外（NFKC正規化＋編集距離＋2-gram Jaccard）</li>
    <li>Flask単体での非同期ジョブ管理と進捗API</li>
    <li>UIはシンプルなHTML/CSS + Vanilla JSで実装</li>
  </ul>
</section>

<section>
  <h2>ライセンス</h2>
  <p>MIT</p>
</section>

</body>
</html>
