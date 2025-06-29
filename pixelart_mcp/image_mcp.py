from mcp.server.fastmcp import FastMCP
from typing import Any, Literal, Annotated

from pydantic import BaseModel
from image_jobs import ImageJobManager, ImageJobInfo

class aaa(BaseModel):
    job_id: str


mcp = FastMCP("PixelArt Image MCP")
job_manager = ImageJobManager()

@mcp.tool(
    title="プロンプト(英文)から画像を生成します。",
    description="Stable Diffusion等のモデルを用いて、指定したプロンプト(英文)から画像を生成します。"
)
def generate_image_tool(
    prompt: str,
    width: int = 512,
    height: int = 512,
) -> dict[str, Any]:
    """
    画像生成ジョブを投入し、ジョブIDを返す
    """
    job_id = job_manager.submit_image_job(prompt, width, height)
    return {"job_id": job_id}

@mcp.tool(
    title="プロンプト(英文)からピクセルアート画像を生成します。",
    description="指定したプロンプト(英文)からピクセルアート画像を生成します。"
)
def generate_pixelart_tool(
    prompt: str,
    pixel_art_mode: Literal[32, 48, 64, 128] = 64,
) -> dict[str, Any]:
    """
    ピクセルアート生成ジョブを投入し、ジョブIDを返す
    """
    job_id = job_manager.submit_pixelart_job(prompt,pixel_art_mode)
    return {"job_id": job_id}

@mcp.tool(
    title="ジョブ一覧を取得します。",
    description="完了・キャンセル・実行中のジョブの一覧を返します。"
)
def list_jobs_tool() -> list[ImageJobInfo]:
    """
    ジョブ一覧を取得する
    """
    return job_manager.list_jobs()

@mcp.tool(
    title="ジョブ詳細を取得します。",
    description="指定したジョブIDの詳細情報とログを返します。"
)
def get_job_tool(job_id: str) -> ImageJobInfo:
    """
    ジョブ詳細を取得する
    """
    return job_manager.get_job(job_id)

@mcp.tool(
    title="ジョブをキャンセルします。",
    description="指定したジョブIDのジョブをキャンセルして停止させます。"
)
def cancel_job_tool(job_id: str) -> str:
    """
    ジョブをキャンセルする
    """
    return job_manager.cancel_job(job_id)

@mcp.tool(
    title="ジョブを削除します。",
    description="指定したジョブIDのジョブを削除します。"
)
def get_image_tool(job_id: str, output_path:str) -> str:
    """
    ジョブを削除する
    """
    return job_manager.get_image(job_id, output_path)

if __name__ == "__main__":
    mcp.run()
