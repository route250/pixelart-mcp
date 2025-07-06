#!/usr/bin/env python3
"""Generate pixel-art images using Stable Diffusion 1.5 with LoRA."""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Iterable

import torch
from diffusers import DiffusionPipeline
from diffusers.schedulers import LCMScheduler
from PIL import Image

PIXELART_LORA = "artificialguybr/pixelartredmond-1-5v-pixel-art-loras-for-sd-1-5"
LCM_LORA = "latent-consistency/lcm-lora-sd15"
BASE_MODEL = "runwayml/stable-diffusion-v1-5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stable Diffusion pixel-art LoRA demo")
    parser.add_argument("--prompt", required=True, help="Text prompt for generation")
    parser.add_argument("--out", default="./outputs", help="Output directory")
    parser.add_argument("--size", type=int, choices=[32, 48, 64, 128], default=64, help="Output pixel size")
    parser.add_argument("--steps", type=int, default=20, help="Sampling steps without LCM")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--device", choices=["mps", "cuda", "cpu"], default="mps", help="Torch device")
    parser.add_argument("--use_lcm", action="store_true", help="Enable LCM-LoRA for fast sampling")
    return parser.parse_args()


def get_device(name: str) -> torch.device:
    if name == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    if name == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_adapters(pipe: DiffusionPipeline, adapters: Iterable[str]) -> None:
    pipe.set_adapters(list(adapters))


def main() -> None:
    args = parse_args()
    device = get_device(args.device)

    steps: int = args.steps
    if args.use_lcm:
        steps = 4 if args.steps == 20 else args.steps

    generator = torch.Generator(device=device)
    seed: int | None = args.seed
    if seed is not None:
        generator = generator.manual_seed(seed)

    pipe = DiffusionPipeline.from_pretrained(BASE_MODEL, torch_dtype=torch.float16)
    pipe = pipe.to(device)

    pipe.load_lora_weights(PIXELART_LORA, adapter_name="pixel")
    adapters = ["pixel"]

    if args.use_lcm:
        pipe.load_lora_weights(LCM_LORA, adapter_name="lcm")
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
        adapters.append("lcm")

    set_adapters(pipe, adapters)
    pipe.set_progress_bar_config(disable=True)

    t0 = time.time()
    imgs = pipe(
        prompt=args.prompt,
        num_inference_steps=steps,
        generator=generator,
        width=512,
        height=512,
    ).images
    elapsed = time.time() - t0

    img = imgs[0].resize((args.size, args.size), Image.NEAREST)
    # img = imgs[0].resize((args.size, args.size), Image.NEAREST)  # sharpen pixels

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"output_{int(time.time())}.png"
    img.save(out_path)
    print(f"Saved to {out_path} ({elapsed:.2f}s)")


if __name__ == "__main__":
    main()
