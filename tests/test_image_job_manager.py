import os
import shutil
import time
import pytest
from pixelart_mcp.image_jobs import ImageJobManager

TEST_IMAGE_DIR = "./tmp/ImageDir"

@pytest.fixture(autouse=True)
def clean_test_dir():
    if os.path.isdir(TEST_IMAGE_DIR):
        shutil.rmtree(TEST_IMAGE_DIR)
    yield
    if os.path.isdir(TEST_IMAGE_DIR):
        shutil.rmtree(TEST_IMAGE_DIR)

def test_submit_and_get_job():
    mgr = ImageJobManager(image_dir=TEST_IMAGE_DIR)
    params = {
        "prompt": "debug",
        "width": 64,
        "height": 64,
        "output_file": "dummy.png"
    }
    job_id = mgr.submit_image_job(params)
    # 投入直後はrunning
    job = mgr.get_job(job_id)
    assert job["job_id"] == job_id
    assert job["status"] == "running"
    assert job["params"]["prompt"] == "debug"
    # 完了まで待機（最大10秒）
    for _ in range(20):
        job = mgr.get_job(job_id)
        if job["status"] in ("finished", "failed"):
            break
        time.sleep(0.5)
    assert job["status"] in ("finished", "failed")
    assert os.path.isfile(os.path.join(TEST_IMAGE_DIR, "jobs", job_id, "job.json"))
    assert os.path.isfile(os.path.join(TEST_IMAGE_DIR, "jobs", job_id, "image.log"))

def test_list_jobs_and_delete():
    mgr = ImageJobManager(image_dir=TEST_IMAGE_DIR)
    params = {"prompt": "test", "output_file": "a.png"}
    job_id = mgr.submit_image_job(params)
    # 完了まで待機
    for _ in range(20):
        jobs = mgr.list_jobs()
        if jobs and jobs[0]["status"] in ("finished", "failed"):
            break
        time.sleep(0.5)
    jobs = mgr.list_jobs()
    assert any(j["job_id"] == job_id for j in jobs)
    mgr.delete_job(job_id)
    jobs = mgr.list_jobs()
    assert not any(j["job_id"] == job_id for j in jobs)

def test_cancel_job():
    mgr = ImageJobManager(image_dir=TEST_IMAGE_DIR)
    params = {"prompt": "cancel", "output_file": "b.png"}
    job_id = mgr.submit_image_job(params)
    # すぐキャンセル
    mgr.cancel_job(job_id)
    job = mgr.get_job(job_id)
    assert job["status"] in ("canceled", "finished", "failed")
