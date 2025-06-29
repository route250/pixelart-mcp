

# ライブラリ

mcp-python-sdkは、mcpサーバを開発するためのライブラリです。

## インストール・利用時の注意

- pipでインストールする場合は `pip install "mcp[cli]"` を使用してください（PyPIパッケージ名はmcp）。
- importパスは `from mcp.server.fastmcp import FastMCP` を推奨します。
- MCPサーバのtool登録は `@mcp.tool` デコレータ方式を推奨します。

repo:https://github.com/modelcontextprotocol/python-sdk

offline documents:
 - docs/mcp-python-skd-README.md
