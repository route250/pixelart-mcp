import unittest
import asyncio
import os
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TestImageMcp(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        print("asyncSetUp: start")
        self.output_dir = "test_output"
        os.makedirs(self.output_dir, exist_ok=True)

        self.log_file = "tmp/test_mcp.log"
        # サーバ起動時に--log-fileを指定
        print("asyncSetUp: before StdioServerParameters")
        server_params = StdioServerParameters(
            command=".venv/bin/python3",
            args=["-m", "pixelart_mcp.image_mcp", "--log-file", self.log_file],
        )
        print("asyncSetUp: before stdio_client")
        self.client = stdio_client(server_params)
        print("asyncSetUp: before __aenter__")
        read, write = await self.client.__aenter__()
        print("asyncSetUp: after __aenter__")
        self.session = ClientSession(read, write)
        print("asyncSetUp: after ClientSession")

        # ログ監視タスク起動
        self._log_monitor_stop = asyncio.Event()
        self._log_monitor_task = asyncio.create_task(self._monitor_log_file())

        print("asyncSetUp: before session.initialize")
        await self.session.initialize()
        print("asyncSetUp: after session.initialize")
        print("asyncSetUp: end")

    async def _monitor_log_file(self):
        """ログファイルの内容を監視し、更新があれば表示する"""

        last_size = 0
        while not self._log_monitor_stop.is_set():
            try:
                if os.path.exists(self.log_file):
                    size = os.path.getsize(self.log_file)
                    if size > last_size:
                        with open(self.log_file, "r") as f:
                            f.seek(last_size)
                            new_content = f.read()
                            if new_content:
                                print("[LOG UPDATE]", new_content, end="")
                        last_size = size
            except Exception as e:
                print("[LOG MONITOR ERROR]", e)
            await asyncio.sleep(0.5)

    async def asyncTearDown(self):
        print("asyncTearDown: start")
        # ログ監視タスク停止
        self._log_monitor_stop.set()
        await self._log_monitor_task
        await self.client.__aexit__(None, None, None)
        print("asyncTearDown: end")

    async def test_generate_image(self):
        print("test_generate_image: start")
        # 画像生成ジョブを投入
        result = await self.session.call_tool("generate_image_tool", {"prompt": "debug", "width": 128, "height": 128})
        result = dict(result)
        print("test_generate_image: job submit result", result, type(result), dir(result))
        self.assertIn("job_id", result)
        job_id = result["job_id"]["job_id"]

        # ジョブが完了するまで待機
        while True:
            job_info = await self.session.call_tool("get_job_tool", {"job_id": job_id})
            job_info = dict(job_info)
            print("test_generate_image: job_info", job_info)
            if job_info["status"] in ["finished", "failed", "canceled"]:
                break
            await asyncio.sleep(1)

        self.assertEqual(job_info["status"], "finished")

        # 画像を取得
        output_path = os.path.join(self.output_dir, f"{job_id}.png")
        get_image_result = await self.session.call_tool("get_image_tool", {"job_id": job_id, "output_path": output_path})
        get_image_result = str(get_image_result)
        print("test_generate_image: get_image_result", get_image_result)
        self.assertEqual(get_image_result, "success, copy image to " + output_path)
        self.assertTrue(os.path.exists(output_path))
        print("test_generate_image: end")

    async def test_generate_pixelart(self):
        print("test_generate_pixelart: start")
        # ピクセルアート生成ジョブを投入
        result = await self.session.call_tool("generate_pixelart_tool", {"prompt": "debug", "pixel_art_mode": 32})
        result = dict(result)
        print("test_generate_pixelart: job submit result", result, type(result), dir(result))
        self.assertIn("job_id", result)
        job_id = result["job_id"]["job_id"]

        # ジョブが完了するまで待機
        while True:
            job_info = await self.session.call_tool("get_job_tool", {"job_id": job_id})
            job_info = dict(job_info)
            print("test_generate_pixelart: job_info", job_info)
            if job_info["status"] in ["finished", "failed", "canceled"]:
                break
            await asyncio.sleep(1)

        self.assertEqual(job_info["status"], "finished")

        # 画像を取得
        output_path = os.path.join(self.output_dir, f"{job_id}.png")
        get_image_result = await self.session.call_tool("get_image_tool", {"job_id": job_id, "output_path": output_path})
        get_image_result = str(get_image_result)
        print("test_generate_pixelart: get_image_result", get_image_result)
        self.assertEqual(get_image_result, "success, copy image to " + output_path)
        self.assertTrue(os.path.exists(output_path))
        print("test_generate_pixelart: end")

if __name__ == '__main__':
    unittest.main()
