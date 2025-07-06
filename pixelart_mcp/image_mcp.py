if __name__ == "__main__":
    import sys,os
    sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp.server.fastmcp import FastMCP
from typing import Any, Literal, Annotated

import logging
logger = logging.getLogger(__name__)


from pydantic import BaseModel
from pixelart_mcp.image_jobs import ImageJobManager, ImageJobInfo

class aaa(BaseModel):
    job_id: str


def create_mcp():
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
        title="ジョブで生成された画像を取得します。",
        description="指定したジョブIDのジョブで生成された画像を取得します。"
    )
    def get_image_tool(job_id: str, output_path:str) -> str:
        """
        ジョブで生成された画像を取得する
        """
        return job_manager.get_image(job_id, output_path)

    return mcp

def run_mcp():
    import sys, os
    import argparse

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    parser = argparse.ArgumentParser()
    parser.add_argument("--log-file", type=str, default="tmp/test.log", help="ログファイルパス")
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_file,
        filemode="w",
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG,
    )

    logger.info("run_mcp: start")
    mcp = create_mcp()
    logger.info("run_mcp: before mcp.run()")
    mcp.run()
    logger.info("run_mcp: after mcp.run()")

if __name__ == "__main__":
    run_mcp()
