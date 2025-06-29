from __future__ import annotations

import os
import time
import json
from typing import Any, ClassVar
import uuid

from datetime import datetime
from pathlib import Path

import multiprocessing
import threading

from typing import Any
from .image_generator import generate_image

def _worker_main(job_queue: Any, jobs_dir: str, ready_event: Any) -> None:


    print("[ImageJobManager] ワーカープロセス開始")
    ready_event.set()
    while True:
        job = job_queue.get()
        if job is None:
            print("[ImageJobManager] ワーカープロセス終了")
            break
        job_id = job["job_id"]
        params = job["params"]
        job_dir = os.path.join(jobs_dir, job_id)
        job_json_path = os.path.join(job_dir, "job.json")
        log_path = os.path.join(job_dir, "image.log")
        start_time = datetime.now()
        try:
            with open(log_path, "w", encoding="utf-8") as logf:
                try:
                    generate_image(
                        prompt=params["prompt"],
                        output_file=params.get("output_file", "output.png"),
                        model_id_key=params.get("model_id_key", "default"),
                        size=(params.get("width", 512), params.get("height", 512)),
                        steps=params.get("steps", 75),
                        resize_to=(params.get("resize_width"), params.get("resize_height")) if params.get("resize_width") and params.get("resize_height") else None,
                        pixel_art_mode=params.get("pixel_art_mode"),
                    )
                    ret = 0
                except Exception as e:
                    import traceback
                    logf.write(traceback.format_exc())
                    ret = 1
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            with open(job_json_path, "r", encoding="utf-8") as jf:
                job_json = json.load(jf)
            if ret == 0:
                job_json["status"] = "finished"
            else:
                job_json["status"] = "failed"
            job_json["end_time"] = end_time.astimezone().isoformat()
            job_json["elapsed"] = elapsed
            with open(job_json_path, "w", encoding="utf-8") as jf:
                json.dump(job_json, jf, ensure_ascii=False, indent=2)
        except Exception as e:
            with open(job_json_path, "r", encoding="utf-8") as jf:
                job_json = json.load(jf)
            job_json["status"] = "failed"
            job_json["end_time"] = datetime.now().astimezone().isoformat()
            job_json["elapsed"] = None
            job_json["error"] = str(e)
            with open(job_json_path, "w", encoding="utf-8") as jf:
                json.dump(job_json, jf, ensure_ascii=False, indent=2)

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
        self._job_queue: Any = multiprocessing.Queue()
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

    def submit_image_job(self, params: dict[str, Any]) -> str:
        """
        通常画像生成ジョブを投入し、ジョブIDを返す。
        :param params: 生成パラメータ
        :return: ジョブID
        """

        job_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        job_dir = os.path.join(self.jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)

        job_json = {
            "job_id": job_id,
            "status": "running",
            "start_time": datetime.now().astimezone().isoformat(),
            "end_time": None,
            "elapsed": None,
            "params": params,
            "output_file": params.get("output_file", ""),
            "log_file": "image.log"
        }
        job_json_path = os.path.join(job_dir, "job.json")
        with open(job_json_path, "w", encoding="utf-8") as f:
            json.dump(job_json, f, ensure_ascii=False, indent=2)

        # ワーカープロセスにジョブを投入
        self._job_queue.put({
            "job_id": job_id,
            "params": params
        })
        return job_id

    def submit_pixelart_job(self, params: dict[str, Any]) -> str:
        """
        ピクセルアート生成ジョブを投入し、ジョブIDを返す。
        :param params: 生成パラメータ
        :return: ジョブID
        """

        job_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]
        job_dir = os.path.join(self.jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)

        job_json = {
            "job_id": job_id,
            "status": "running",
            "start_time": datetime.now().astimezone().isoformat(),
            "end_time": None,
            "elapsed": None,
            "params": params,
            "output_file": params.get("output_file", ""),
            "log_file": "image.log"
        }
        job_json_path = os.path.join(job_dir, "job.json")
        with open(job_json_path, "w", encoding="utf-8") as f:
            json.dump(job_json, f, ensure_ascii=False, indent=2)

        # ワーカープロセスにジョブを投入
        self._job_queue.put({
            "job_id": job_id,
            "params": params
        })
        return job_id

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
