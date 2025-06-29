import os
import torch
import torch.version as torch_version
from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline
from PIL import Image
import numpy as np
from typing import Literal

import time

MODEL_IDS = {
    "default": "runwayml/stable-diffusion-v1-5",
    "s2": "stabilityai/stable-diffusion-2-1",
    "s1": "runwayml/stable-diffusion-v1-5",
    "p1": "PublicPrompts/All-In-One-Pixel-Model",
}

def get_best_device() -> torch.device:
    """
    利用可能なデバイスを優先順位(cuda > mps > cpu)で返す
    """
    if torch.cuda.is_available():
        print("[INFO] CUDAが利用可能です。GPUを使用します。")
        print(f"[INFO] CUDAバージョン: {torch_version.cuda}")
        print(f"[INFO] 利用可能なGPU数: {torch.cuda.device_count()}")
        if torch.backends.cudnn.enabled:
            print(f"[INFO] cuDNNバージョン: {torch.backends.cudnn.version()}")
        else:
            print("[WARNING] cuDNNは無効です。パフォーマンスが低下する可能性があります。")
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("[INFO] MPSが利用可能です。Apple Silicon GPUを使用します。")
        return torch.device("mps")
    else:
        print("[INFO] CPUのみ利用可能です。")
        return torch.device("cpu")

def generate_image(
    prompt: str,
    output_file: str,
    model_id_key: str = "default",
    size: tuple[int, int] = (512, 512),
    steps: int = 75,
    resize_to: tuple[int, int] | None = None,
    pixel_art_mode: Literal[None, 32, 48, 64, 128] = None,
):
    if pixel_art_mode is not None and resize_to is not None:
        raise ValueError("resize_toとpixel_art_modeは同時に指定できません。どちらか一方のみ指定してください。")
    elif pixel_art_mode is not None:
        if model_id_key == "default":
            model_id_key = "p1"
        size = (512, 512)
        resize_to = (int(pixel_art_mode), int(pixel_art_mode))
    else:
        if model_id_key == "default":
            model_id_key = "s1"

    model_id = MODEL_IDS.get(model_id_key, MODEL_IDS["default"])

    print(f"[INFO] プロンプト: {prompt}")
    print(f"[INFO] 生成サイズ: {size[0]}x{size[1]}")
    if pixel_art_mode is not None:
        print(f"[INFO] ピクセルアート化サイズ: {pixel_art_mode}x{pixel_art_mode}")
    elif resize_to is not None:
        print(f"[INFO] リサイズ前のサイズ: {resize_to[0]}x{resize_to[1]}")
    print(f"[INFO] モデルIDキー: {model_id}")
    print(f"[INFO] 推論ステップ数: {steps}")
    print(f"[INFO] 出力ファイル: {output_file}")

    if "debug" in prompt:
        time.sleep(3)
        dummy_image = Image.new("RGB", size, (128, 128, 128))
        dummy_image.save(output_file)
        print(f"[DEBUG] ダミー画像を保存しました: {output_file}")
        return
    device = get_best_device()

    os.environ["HF_HOME"] = "/fs/hdd1/hugging_face_cache"
    print(f"[INFO] モデル読み込み中 ({model_id})...")

    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        safety_checker=None,
        torch_dtype=torch.float32
    ).to(device)

    print(f"[INFO] 画像生成中... Prompt: {prompt}")

    result = pipe(prompt, num_inference_steps=steps, height=size[1], width=size[0])

    image = getattr(result, "images", result[0])

    if not isinstance(image, Image.Image):
        if isinstance(image, torch.Tensor):
            image = image.cpu().numpy()
        elif not isinstance(image, np.ndarray):
            image = np.array(image)
        print(type(image), getattr(image, "shape", None))
        while hasattr(image, "ndim") and image.ndim > 3:
            image = np.squeeze(image, axis=0)
        print(type(image), getattr(image, "shape", None))
        image = Image.fromarray(image)

    if resize_to is not None:
        resample = Image.NEAREST if pixel_art_mode else Image.LANCZOS  # type: ignore
        image = image.resize(resize_to, resample=resample)
        print(f"[INFO] 画像をリサイズ: {resize_to[0]}x{resize_to[1]} (pixel_art_mode={pixel_art_mode})")

    image.save(output_file)
    print(f"[DONE] 保存完了: {output_file}")

def parse_size(size_str: str) -> tuple[int, int]:
    """WIDTHxHEIGHT形式の文字列を(int, int)に変換"""
    try:
        width, height = map(int, size_str.lower().split("x"))
        return width, height
    except Exception:
        raise ValueError("サイズは WIDTHxHEIGHT 形式で指定してください (例: 512x256)")
