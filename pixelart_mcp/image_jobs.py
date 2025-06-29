from __future__ import annotations

from enum import Enum
import os
import time
import json
from typing import Any, ClassVar, Literal
import uuid

from datetime import datetime
from pathlib import Path

import multiprocessing
import threading

from typing import Any

from pydantic import BaseModel
from .image_generator import generate_image

class JobStatus(Enum):
    not_start = "not_start"
    running = "running"
    finished = "finished"
    failed = "failed"
    canceled = "canceled"

class ImageJobInfo(BaseModel):
    job_id: str
    status: JobStatus
    start_time: str
    end_time: str | None = None
    elapsed: float | None = None
    prompt: str
    image_width: int | None = None
    image_height: int | None = None
    pixel_art_size: Literal[None, 32, 48, 64, 128] = None
    output_path: str = ""

    @staticmethod
    def new_image(prompt:str, width:int, height:int, output_path:str) -> ImageJobInfo:
        """
        新しい画像生成ジョブを作成する
        :param prompt: 生成する画像のプロンプト
        :param width: 画像の幅
        :param height: 画像の高さ
        :param output_path: 出力先パス
        :return: ImageJobInfoインスタンス
        """
        job_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        return ImageJobInfo(
            job_id=job_id,
            status=JobStatus.not_start,
            start_time=datetime.now().astimezone().isoformat(),
            prompt=prompt,
            image_width=width,
            image_height=height,
            output_path=output_path
        )

    @staticmethod
    def new_pixelart(prompt:str, pixel_art_size:Literal[None, 32, 48, 64, 128], output_path:str) -> ImageJobInfo:
        """
        新しいピクセルアート生成ジョブを作成する
        :param prompt: 生成するピクセルアートのプロンプト
        :param pixel_art_size: ピクセルアートのサイズ（32, 48, 64, 128）
        :param output_path: 出力先パス
        :return: ImageJobInfoインスタンス
        """
        job_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        return ImageJobInfo(
            job_id=job_id,
            status=JobStatus.not_start,
            start_time=datetime.now().astimezone().isoformat(),
            prompt=prompt,
            pixel_art_size=pixel_art_size,
            output_path=output_path
        )

    @staticmethod
    def load(job_json_path: str) -> ImageJobInfo:
        """
        job.jsonからジョブ情報を読み込み、ImageJobInfoインスタンスを返す
        :param job_json_path: job.jsonのパス
        :return: ImageJobInfoインスタンス
        """
        with open(job_json_path, "r", encoding="utf-8") as f:
            job_data = json.load(f)
        return ImageJobInfo(**job_data)

    def set_start(self) -> None:
        """
        ジョブのステータスをrunningに設定し、開始時刻を更新する
        """
        self.status = JobStatus.running
        self.start_time = datetime.now().astimezone().isoformat()
    def set_finished(self) -> None:
        """
        ジョブのステータスをfinishedに設定し、終了時刻と経過時間を更新する
        """
        self.status = JobStatus.finished
        self.end_time = datetime.now().astimezone().isoformat()
        if self.start_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.elapsed = (end - start).total_seconds()
    def set_failed(self, error: str) -> None:
        """
        ジョブのステータスをfailedに設定し、終了時刻とエラー内容を更新する
        :param error: エラーメッセージ
        """
        self.status = JobStatus.failed
        self.end_time = datetime.now().astimezone().isoformat()
        if self.start_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.elapsed = (end - start).total_seconds()
        self.error = error
    def save(self, job_json_path: str) -> None:
        """
        ImageJobInfoインスタンスの内容をjob.jsonに保存する
        :param job_json_path: 保存先のjob.jsonパス
        """
        with open(job_json_path, "w", encoding="utf-8") as f:
            json.dump(self.dict(), f, ensure_ascii=False, indent=2)
    
def _worker_main(job_queue: Any, jobs_dir: str, ready_event: Any) -> None:


    print("[ImageJobManager] ワーカープロセス開始")
    ready_event.set()
    while True:
        job_id = job_queue.get()
        if job_id is None:
            print("[ImageJobManager] ワーカープロセス終了")
            break
        try:
            job_dir = os.path.join(jobs_dir, job_id)
            job_json_path = os.path.join(job_dir, "job.json")

            log_path = os.path.join(job_dir, "image.log")

            job_info = ImageJobInfo.load(job_json_path)
            job_info.set_start()
            job_info.save(job_json_path)

            try:
                if job_info.pixel_art_size is None:
                    h = job_info.image_height or 512
                    w = job_info.image_width or 512
                    generate_image(
                        prompt=job_info.prompt,
                        size=(h,w),
                        output_file=job_info.output_path,
                    )
                else:
                    generate_image(
                        prompt=job_info.prompt,
                        pixel_art_mode=job_info.pixel_art_size,
                        output_file=job_info.output_path,
                    )
                job_info.set_finished()
            except Exception as e:
                import traceback
                logf.write(traceback.format_exc())
                job_info.set_failed(str(e))
            finally:
                job_info.save(job_json_path)

        except Exception as e:
            break

class ImageJobManager:
    """
    画像生成ジョブの管理クラス。
    ジョブ投入、状態取得、リスト、キャンセル、削除、永続化を担当する。
    """

    DEFAULT_IMAGE_DIR: ClassVar[str] = os.path.expanduser("~/.cache/image_mcp")

    def __init__(self, image_dir: str | None = None) -> None:
        """
        :param image_dir: ジョブ・ログ等を保存するディレクトリ（デフォルト: ~/.cache/image_mcp）
        """
        self.image_dir = image_dir or self.DEFAULT_IMAGE_DIR
        self.jobs_dir = os.path.join(self.image_dir, "jobs")
        os.makedirs(self.jobs_dir, exist_ok=True)
        # ワーカープロセス起動
        self._job_queue: multiprocessing.Queue[str] = multiprocessing.Queue()
        self._ready_event: Any = multiprocessing.Event()
        print("[ImageJobManager] ワーカープロセスを起動します")
        self._worker_process: multiprocessing.Process = multiprocessing.Process(
                target=_worker_main,
                args=(self._job_queue, self.jobs_dir, self._ready_event),
                daemon=True
            )
        self._worker_process.start()
        print(f"[ImageJobManager] ワーカープロセスPID: {self._worker_process.pid}")
        self._ready_event.wait()
        print("[ImageJobManager] ワーカープロセス ready")

    def submit_image_job(self, prompt:str, width:int, height:int, output_path:str ) -> ImageJobInfo:
        """
        Submits an image generation job and returns the job ID.

        Args:
            prompt (str): The prompt or description for image generation.
            width (int): The width of the generated image.
            height (int): The height of the generated image.
            output_path (str): The file path where the generated image will be saved.

        Returns:
            ImageJobInfo: Information about the submitted image job.

        Raises:
            OSError: If the job directory cannot be created.
            Exception: For other unexpected errors during job submission.

        Note:
            This method creates a unique job directory, saves job metadata as a JSON file,
            and enqueues the job for processing by a worker process.
        """

        job_info = ImageJobInfo.new_image(
            prompt=prompt,
            width=width,
            height=height,
            output_path=output_path
        )

        job_dir = os.path.join(self.jobs_dir, job_info.job_id)
        os.makedirs(job_dir, exist_ok=True)

        job_json_path = os.path.join(job_dir, "job.json")
        job_info.save(job_json_path)

        # ワーカープロセスにジョブを投入
        self._job_queue.put(job_info.job_id)
        return job_info

    def submit_pixelart_job(self, prompt:str, pixel_art_size:Literal[32, 48, 64, 128], output_path:str) -> ImageJobInfo:
        """
        ピクセルアート生成ジョブを投入し、ジョブIDを返す。
        :param params: 生成パラメータ
        :return: ジョブID
        """

        job_info = ImageJobInfo.new_pixelart(
            prompt=prompt,
            pixel_art_size=pixel_art_size,
            output_path=output_path
        )
        job_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        job_dir = os.path.join(self.jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)

        job_json_path = os.path.join(job_dir, "job.json")
        job_info.save(job_json_path)
        return job_info

    def list_jobs(self) -> list[dict[str, Any]]:
        """
        ジョブ一覧を取得する。
        :return: 各ジョブのjob_id, status, 時刻, params等を含むリスト
        """
        jobs: list[dict[str, Any]] = []
        jobs_path = Path(self.jobs_dir)
        for job_json_path in jobs_path.glob("*/job.json"):
            try:
                with open(job_json_path, "r", encoding="utf-8") as f:
                    job = json.load(f)
                jobs.append(job)
            except Exception:
                # job.jsonが壊れている場合はスキップ
                continue
        # start_time降順でソート
        jobs.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return jobs

    def get_job(self, job_id: str) -> dict[str, Any]:
        """
        指定ジョブの詳細情報を取得する。
        :param job_id: ジョブID
        :return: ジョブ詳細情報（job.json内容＋ログ等）
        """
        job_dir = os.path.join(self.jobs_dir, job_id)
        job_json_path = os.path.join(job_dir, "job.json")
        if not os.path.isfile(job_json_path):
            raise KeyError(f"job_id not found: {job_id}")
        with open(job_json_path, "r", encoding="utf-8") as f:
            job = json.load(f)
        log_path = os.path.join(job_dir, "image.log")
        if os.path.isfile(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as lf:
                job["job_log"] = lf.read()
        else:
            job["job_log"] = None
        return job

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        """
        実行中ジョブをキャンセルする。
        :param job_id: ジョブID
        :return: ジョブ詳細情報
        """
        job_dir = os.path.join(self.jobs_dir, job_id)
        job_json_path = os.path.join(job_dir, "job.json")
        if not os.path.isfile(job_json_path):
            raise KeyError(f"job_id not found: {job_id}")
        with open(job_json_path, "r", encoding="utf-8") as f:
            job = json.load(f)
        if job.get("status") == "running":
            job["status"] = "canceled"
            job["end_time"] = datetime.now().astimezone().isoformat()
            try:
                start = datetime.fromisoformat(job["start_time"])
                end = datetime.fromisoformat(job["end_time"])
                job["elapsed"] = (end - start).total_seconds()
            except Exception:
                job["elapsed"] = None
            with open(job_json_path, "w", encoding="utf-8") as f:
                json.dump(job, f, ensure_ascii=False, indent=2)
        # 最新状態を返す
        return self.get_job(job_id)

    def delete_job(self, job_id: str) -> None:
        """
        ジョブを削除する。
        :param job_id: ジョブID
        """
        import shutil

        job_dir = os.path.join(self.jobs_dir, job_id)
        if not os.path.isdir(job_dir):
            raise KeyError(f"job_id not found: {job_id}")
        shutil.rmtree(job_dir)

if __name__ == "__main__":
    print("[ImageJobManager] このファイルは直接実行できません。")
