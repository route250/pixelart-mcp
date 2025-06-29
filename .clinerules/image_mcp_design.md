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
  - ジョブ投入、状態取得、リスト取得、キャンセル、削除
  - ジョブ情報の永続化（job.json, image.log等）

---

## 2. クラス設計

### ImageJobManager

| メソッド                | 概要                                             |
|-------------------------|--------------------------------------------------|
| submit_image_job(params: dict) -> str   | 画像生成ジョブ投入、ジョブID返却            |
| submit_pixelart_job(params: dict) -> str| ピクセルアートジョブ投入、ジョブID返却       |
| list_jobs() -> list[dict]               | ジョブ一覧取得                              |
| get_job(job_id: str) -> dict            | ジョブ詳細取得                              |
| cancel_job(job_id: str) -> dict         | ジョブキャンセル                            |
| delete_job(job_id: str)                 | ジョブ削除                                  |

#### Jobデータ構造（job.json例）

```json
{
  "job_id": "xxxxxx",
  "status": "running|finished|canceled|failed",
  "start_time": "2025-06-28T23:00:00+09:00",
  "end_time": "2025-06-28T23:01:00+09:00",
  "elapsed": 60.0,
  "params": { ... },
  "output_file": "output.png",
  "log_file": "image.log"
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
| output_file     | str          | 出力ファイルパス           |

- 戻り値: ジョブID（str）

### generate_pixelart_tool

| パラメータ      | 型           | 説明                       |
|-----------------|--------------|----------------------------|
| prompt          | str          | 生成プロンプト             |
| pixel_art_mode  | 32/48/64/128 | ピクセルアートサイズ       |
| output_file     | str          | 出力ファイルパス           |

- 戻り値: ジョブID（str）

### list_jobs_tool

- パラメータ: なし
- 戻り値: list[dict]（各ジョブのjob_id, status, 時刻, params等）

### get_job_tool

| パラメータ | 型  | 説明   |
|------------|-----|--------|
| job_id     | str | ジョブID |

- 戻り値: dict（ジョブ詳細、ログ等）

### cancel_job_tool

| パラメータ | 型  | 説明   |
|------------|-----|--------|
| job_id     | str | ジョブID |

- 戻り値: dict（ジョブ詳細）

### delete_job_tool

| パラメータ | 型  | 説明   |
|------------|-----|--------|
| job_id     | str | ジョブID |

---

## 4. データディレクトリ・ファイル構成

- {ImageDir}/（デフォルト: $HOME/.cache/image_mcp）
  - logs/*.log … サーバ実行ログ
  - jobs/xxxxxx/ … ジョブごとのディレクトリ（xxxxxx=ジョブID）
    - image.log … 生成処理ログ
    - job.json … 実行状態・内容
    - その他一時ファイル等

---

## 5. 主要処理フロー

1. ユーザーがMCPツール（generate_image_tool等）を呼び出す
2. image_mcp.pyがリクエストを受け、ImageJobManagerに処理を委譲
3. ImageJobManagerがジョブディレクトリ作成・job.json保存・バックグラウンドで生成処理開始
4. ジョブ状態はlist_jobs_tool/get_job_toolで確認可能
5. 完了後、output_fileに画像が保存される

---

以上が詳細設計案です。

---

## 実装ToDoリスト
- ToDoリストの進捗チェックは、実装完了時に[x]を付与し、常に最新状態を保つこと。複数人・複数タスク並行時も一貫性を担保するため、編集履歴やコミットコメントにも進捗反映内容を明記すること。
- MCPツール実装時は、PEP 585/604型ヒント・docstring・バリデーション・エラー処理を必ず記述し、推奨スタイル例を参照すること（例: 引数型はlist[str]、戻り値はdict[str,Any]等）。
- 複数ファイル横断で設計反映・ToDo進捗を行う場合、diff例や注意点（SEARCH/REPLACEブロックの厳密一致、空白・コメント行の扱い等）をTipsとして追記すること。
- CLI/ロジック分割時は、import構成・依存関係・choices値の整合性（例: choices=["off", "32", ...]とロジック側のLiteral型の一致）を必ず確認し、不要な値やスペルミスがあれば修正すること。
- CLI分割後は、元ファイルの削除やテスト動作確認手順もToDoに含めること。
- PEP 585/604型ヒントの具体例や注意点（古い型ヒントとの違い、VSCode補完・型チェッカー対応状況等）もまとめておくこと。

処理が完了項目にはマークをつけること。常にToDoリストを更新し不足している作業を追加して管理すること

- [x] image_jobs.py: ImageJobManagerクラスの作成
    - [x] submit_image_jobの実装
    - [x] submit_pixelart_jobの実装
    - [x] list_jobsの実装
    - [x] get_jobの実装
    - [x] cancel_jobの実装
    - [x] delete_jobの実装
    - [x] ジョブ情報の永続化（job.json, image.log等）

- [x] image_mcp.py: MCPサーバ本体の作成
    - [x] FastMCPインスタンス生成
    - [x] generate_image_toolの登録・実装
    - [x] generate_pixelart_toolの登録・実装
    - [x] list_jobs_toolの登録・実装
    - [x] get_job_toolの登録・実装
    - [x] cancel_job_toolの登録・実装
    - [x] delete_job_toolの登録・実装
    - [x] image_jobs.pyの管理クラス呼び出し

- [ ] 動作確認用CLI（gen_image_cli.py）の利用
    - [ ] 画像生成処理はgen_image_cli.pyの関数呼び出し方式で実装
    - [ ] generate_imageコマンド
    - [ ] generate_pixelartコマンド
    - [ ] model_id_key, steps等のCLI用パラメータ対応
    - [ ] MCPサーバとの連携確認
