# image_mcpの仕様

## 概要

画像生成、ピクセルアート生成を行うMCPプロトコルサーバ  
mcp-python-sdkによる実装で、stdio,sse,streaminghttpをサポート  
see: docs/mcp-python-sdk-README.md  
処理はバックグラウンドジョブ方式で、ジョブキューによるバックグラウンド処理  
ジョブ投入、ジョブ一覧、ジョブキャンセル、画像取得の機能を提供する  
LLMは、ジョブを投入したあと、ジョブリストで確認し、完了していたらリストのファイルパスを使用すればよい。

## 提供するツール

### 画像生成ジョブ投入

通常の画像生成処理を投入する  
パラメータ:  
- 生成プロンプト (prompt: str)  
- 画像サイズ横 (width: int)  
- 画像サイズ縦 (height: int)  
戻り値: dict（{"job_id": str}）

### ピクセルアート投入

ピクセルアート生成処理を投入する  
パラメータ:  
- 生成プロンプト (prompt: str)  
- 生成サイズ (pixel_art_mode: 32, 48, 64, 128)  
戻り値: dict（{"job_id": str}）

### ジョブリスト

完了・キャンセル・実行中のジョブの一覧を返す。  
パラメータ: なし  
戻り値: list[ImageJobInfo]（各ジョブのjob_id, status, 時刻, params等）

### ジョブ取得

ジョブの状態を取得する  
パラメータ:  
- ジョブID (job_id: str)  
戻り値: ImageJobInfo（ジョブ詳細）

### ジョブキャンセル

実行中のジョブをキャンセルして停止させる  
パラメータ:  
- ジョブID (job_id: str)  
戻り値: str（キャンセル結果メッセージ）

### 画像取得

ジョブで生成した画像を指定パスにコピーする  
パラメータ:  
- ジョブID (job_id: str)  
- コピー先ファイルパス (output_path: str)  
戻り値: str（画像コピー結果メッセージ）

## データとか

{ImageDir}/ コマンドラインで指定されるディレクトリ、デフォルトは、$HOME/.cache/image_mcp  
  - logs/*.log  mcpサーバの実行ログ  
  - jobs/xxxxxx/  ジョブのディレクトリ xxxxxxがジョブID  
    - image.log  生成処理のログ  
    - job.json   実行状態、内容などジョブリストに必要な内容  
    - output.png 生成画像  
    - その他ジョブ実行に必要なファイルや一時ファイル
