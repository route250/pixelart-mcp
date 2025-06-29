# image_mcp 詳細設計

## MCP Python SDK 実装ポイント

- MCPサーバは `from mcp.server.fastmcp import FastMCP` で生成し、`mcp = FastMCP("サーバ名")` でインスタンス化する。
- MCPツールは `@mcp.tool()` デコレータで登録し、引数・戻り値に型ヒントを付与することで自動的にスキーマ化・バリデーションされる。
- 戻り値はプリミティブ型、dict、TypedDict、Pydanticモデル、dataclass等で構造化返却が可能。型ヒントがない場合は非構造化返却となる。
- 画像返却には `from mcp.server.fastmcp import Image` を利用し、PIL等で生成した画像データを `Image(data=..., format="png")` で返す。
- Context（`from mcp.server.fastmcp import Context`）をツール引数に追加することで、進捗通知やリソースアクセス、ユーザーへの追加情報要求（elicitation）が可能。
- サーバ起動は `if __name__ == "__main__": mcp.run()` でOK。`mcp.run(transport="streamable-http")` でHTTP対応も可能。
- 開発時は `mcp dev image_mcp.py` でホットリロード・依存追加も可能。
- 詳細はdocs/mcp-python-sdk-README.mdのQuickstart・Examples・Structured Output・Images・Context・Elicitation等を参照。

---

## 1. モジュール構成

- **image_mcp.py**
  - MCPサーバ本体
  - FastMCPインスタンス生成・ツール登録
  - リクエスト受付・レスポンス返却
  - image_jobs.pyの管理クラスを利用

- **image_jobs.py**
  - ジョブ管理・実行ロジック
  - ジョブ投入、状態取得、リスト取得、キャンセル、画像取得
  - ジョブ情報の永続化（job.json, image.log等）

---

## 2. クラス設計

### ImageJobManager

| メソッド                                      | 概要                                             |
|-----------------------------------------------|--------------------------------------------------|
| submit_image_job(prompt:str, width:int, height:int) -> ImageJobInfo   | 画像生成ジョブ投入、ジョブ情報返却                |
| submit_pixelart_job(prompt:str, pixel_art_size:Literal[32,48,64,128]) -> ImageJobInfo | ピクセルアートジョブ投入、ジョブ情報返却           |
| list_jobs() -> list[ImageJobInfo]             | ジョブ一覧取得                                   |
| get_job(job_id: str) -> ImageJobInfo          | ジョブ詳細取得                                   |
| cancel_job(job_id: str) -> str                | ジョブキャンセル、結果メッセージ返却              |
| get_image(job_id: str, output_path: str) -> str | 画像ファイルを指定パスにコピー、結果メッセージ返却 |

#### ImageJobInfoデータ構造（job.json例）

```json
{
  "job_id": "xxxxxx",
  "status": "not_start|running|finished|canceled|failed",
  "start_time": "2025-06-28T23:00:00+09:00",
  "end_time": "2025-06-28T23:01:00+09:00",
  "elapsed": 60.0,
  "prompt": "A cat in pixel art",
  "image_width": 512,
  "image_height": 512,
  "pixel_art_size": 64
}
```

---

## 3. MCPツールインターフェース

### generate_image_tool

| パラメータ      | 型           | 説明                       |
|-----------------|--------------|----------------------------|
| prompt          | str          | 生成プロンプト             |
| width           | int          | 画像幅（ピクセル）         |
| height          | int          | 画像高さ（ピクセル）       |

- 戻り値: dict（{"job_id": str}）

### generate_pixelart_tool

| パラメータ      | 型           | 説明                       |
|-----------------|--------------|----------------------------|
| prompt          | str          | 生成プロンプト             |
| pixel_art_mode  | 32/48/64/128 | ピクセルアートサイズ       |

- 戻り値: dict（{"job_id": str}）

### list_jobs_tool

- パラメータ: なし
- 戻り値: list[ImageJobInfo]（各ジョブのjob_id, status, 時刻, params等）

### get_job_tool

| パラメータ | 型  | 説明   |
|------------|-----|--------|
| job_id     | str | ジョブID |

- 戻り値: ImageJobInfo（ジョブ詳細）

### cancel_job_tool

| パラメータ | 型  | 説明   |
|------------|-----|--------|
| job_id     | str | ジョブID |

- 戻り値: str（キャンセル結果メッセージ）

### get_image_tool

| パラメータ   | 型  | 説明                |
|--------------|-----|---------------------|
| job_id       | str | ジョブID            |
| output_path  | str | コピー先ファイルパス |

- 戻り値: str（画像コピー結果メッセージ）

---

## 4. データディレクトリ・ファイル構成

- {ImageDir}/（デフォルト: $HOME/.cache/image_mcp）
  - logs/*.log … サーバ実行ログ
  - jobs/xxxxxx/ … ジョブごとのディレクトリ（xxxxxx=ジョブID）
    - image.log … 生成処理ログ
    - job.json … 実行状態・内容
    - output.png … 生成画像
    - その他一時ファイル等

---

## 5. 主要処理フロー

1. ユーザーがMCPツール（generate_image_tool等）を呼び出す
2. image_mcp.pyがリクエストを受け、ImageJobManagerに処理を委譲
3. ImageJobManagerがジョブディレクトリ作成・job.json保存・バックグラウンドで生成処理開始
4. ジョブ状態はlist_jobs_tool/get_job_toolで確認可能
5. 完了後、output.pngに画像が保存される

---

以上が詳細設計案です。

---
