from dataclasses import dataclass
import os
import torch
import torch.version as torch_version
from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline
from PIL import Image
import numpy as np
from typing import Literal

import time

@dataclass
class ModelInfo:
    name: str
    description: str
    hf_model_id: str
    hf_lora_id: str|None = None
    typ: str = ""
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    negave_prompt: str = "low quality, worst quality, normal quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, fewer digits, cropped, worst quality, low quality, normal quality, error, missing fingers, extra digit, fewer digits, bad anatomy, bad hands, text, error, missing fingers, extra digit and fewer digits"

MODEL_IDS: dict[str, ModelInfo] = {
    "s1": ModelInfo(
        name="SD‑1.5 Base",
        description="汎用 Stable Diffusion v1.5",
        hf_model_id="runwayml/stable-diffusion-v1-5",
        typ="stable-diffusion",
        prompt_prefix="",
    ),
    "s2": ModelInfo(
        name="SD‑2.1 Base",
        description="汎用 Stable Diffusion v2.1",
        hf_model_id="stabilityai/stable-diffusion-2-1",
        typ="stable-diffusion",
        prompt_prefix="",
    ),
    "p1": ModelInfo(
        name="All-In-One Pixel Model",
        description="for pixel art",
        hf_model_id="PublicPrompts/All-In-One-Pixel-Model",
        typ="stable-diffusion",
        prompt_prefix="pixel art",
    ),
    "par": ModelInfo(
        name="PixelArt.Redmond (SD1.5 LoRA)",
        description="SD1.5 向けドット絵キャラ特化LoRA",
        hf_model_id="runwayml/stable-diffusion-v1-5",
        hf_lora_id="artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5",
        typ="lora-sd1.5",
        prompt_suffix=", pixel art, PixArFK,",
    ),
}
"""
# https://huggingface.co/artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5
"""

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
        if model_id_key not in MODEL_IDS:
            model_id_key = "p1"
        size = (512, 512)
        resize_to = (int(pixel_art_mode), int(pixel_art_mode))
    else:
        if model_id_key not in MODEL_IDS:
            model_id_key = "s1"

    model_info = MODEL_IDS.get(model_id_key)
    if model_info is None:
        print(f"[ERROR] モデルID '{model_id_key}' が見つかりません。")
        return

    print(f"[INFO] プロンプト: {prompt}")
    print(f"[INFO] 生成サイズ: {size[0]}x{size[1]}")
    if pixel_art_mode is not None:
        print(f"[INFO] ピクセルアート化サイズ: {pixel_art_mode}x{pixel_art_mode}")
    elif resize_to is not None:
        print(f"[INFO] リサイズ前のサイズ: {resize_to[0]}x{resize_to[1]}")
    print(f"[INFO] モデル: {model_info.hf_model_id}")
    print(f"[INFO] {model_info.description}")
    print(f"[INFO] 推論ステップ数: {steps}")
    print(f"[INFO] 出力ファイル: {output_file}")

    if "debug" in prompt:
        time.sleep(3)
        dummy_image = Image.new("RGB", size, (128, 128, 128))
        dummy_image.save(output_file)
        print(f"[DEBUG] ダミー画像を保存しました: {output_file}")
        return
    device = get_best_device()

    if os.path.isdir("/fs/hdd1/hugging_face_cache"):
        print(f"[INFO] Hugging Face キャッシュディレクトリを設定: /fs/hdd1/hugging_face_cache")
        os.environ["HF_HOME"] = "/fs/hdd1/hugging_face_cache"
    print(f"[INFO] モデル読み込み中...")

    try:
        pipe = StableDiffusionPipeline.from_pretrained(
            model_info.hf_model_id,
            safety_checker=None,
            torch_dtype=torch.float32
        ).to(device)

        # LoRA を適用する例
        if model_info.hf_lora_id:
            print(f"[INFO] LoRA を読み込み: {model_info.hf_model_id}")
            pipe.load_lora_weights(model_info.hf_lora_id)
    except Exception as e:
        print(f"[ERROR] モデルの読み込みに失敗しました: {e}")
        return
    
    try:
        print(f"[INFO] 画像生成中... Prompt: {prompt}")
        promptx = prompt
        if model_info.prompt_prefix:
            promptx = f"{model_info.prompt_prefix} {prompt}"
        if model_info.prompt_suffix:
            promptx = f"{promptx} {model_info.prompt_suffix}"
        negative_prompt = model_info.negave_prompt
        result = pipe(prompt=promptx, negative_prompt=negative_prompt, num_inference_steps=steps, height=size[1], width=size[0])

        image = getattr(result, "images", result[0])
    except Exception as e:
        print(f"[ERROR] 画像生成に失敗しました: {e}")
        return
    try:
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
    except Exception as e:
        print(f"[ERROR] 画像の変換に失敗しました: {e}")
        return

    try:
        if resize_to is not None:
            resample = Image.NEAREST if pixel_art_mode else Image.LANCZOS  # type: ignore
            image = image.resize(resize_to, resample=resample)
            print(f"[INFO] 画像をリサイズ: {resize_to[0]}x{resize_to[1]} (pixel_art_mode={pixel_art_mode})")
    except Exception as e:
        print(f"[ERROR] 画像のリサイズに失敗しました: {e}")
        return
    try:
        image.save(output_file)
    except Exception as e:
        print(f"[ERROR] 画像の保存に失敗しました: {e}")
        return
    print(f"[DONE] 保存完了: {output_file}")

def parse_size(size_str: str) -> tuple[int, int]:
    """WIDTHxHEIGHT形式の文字列を(int, int)に変換"""
    try:
        width, height = map(int, size_str.lower().split("x"))
        return width, height
    except Exception:
        raise ValueError("サイズは WIDTHxHEIGHT 形式で指定してください (例: 512x256)")
