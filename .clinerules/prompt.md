

# ライブラリ

mcp-python-sdkは、mcpサーバを開発するためのライブラリです。

## インストール・利用時の注意

- pipでインストールする場合は `pip install "mcp[cli]"` を使用してください（PyPIパッケージ名はmcp）。
- importパスは `from mcp.server.fastmcp import FastMCP` を推奨します。
- MCPサーバのtool登録は `@mcp.tool` デコレータ方式を推奨します。

repo:https://github.com/modelcontextprotocol/python-sdk

offline documents:
 - docs/mcp-python-skd-README.md

# タスク管理手順
タスクは、 ToDo.mdで管理すること
1. 未完了なタスクのどのタスクに相当するかを判定して、タスクがなければ、タスクリストに追加
2. タスクを実行、もし必要があれば、新しいタスクを追加したり、タスクを分解したり、修正する
3. タスクが完了したら、タスクリストに完了マークをつけること
タスクの進捗ごとにdevelopment_log.mdで、状況を追記していくこと
