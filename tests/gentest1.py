from dataclasses import dataclass
import sys,os
sys.path.insert(0,'.')
import torch
import torch.version as torch_version
from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline
from PIL import Image
import numpy as np
from typing import Literal

import time

from pixelart_mcp.image_generator import generate_image, parse_size, MODEL_IDS
import logging


def test_s1(prompt):
 
        outpath='tmp/output-test-s1.png'
        generate_image(
            prompt,
            outpath,
            model_id_key='s1',
            #steps=10,
        )

def test_s2(prompt):

        outpath='tmp/output-test-s2.png'
        generate_image(
            prompt,
            outpath,
            model_id_key='s2',
        )

def test_pix( prompt, *, pix:Literal[32,48,64,128,256,512]=128, steps:int=50):

        outpath=f'tmp/output-test-pix{pix}.png'
        generate_image(
            prompt,
            outpath,
            steps=steps,
            pixel_art_mode=pix,
        )

def test_par(prompt):

        outpath='tmp/output-test-par.png'
        generate_image(
            prompt,
            outpath,
            model_id_key='par',
            pixel_art_mode=64,
        )

if __name__ == "__main__":
        logging.basicConfig(level=logging.INFO)
        prompt='white cat, walking, fish'
        test_s1(prompt)
        test_s2(prompt)
        prompt='Godzilla, game asset, white background'
        test_pix(prompt, pix=512)
        test_pix(prompt, pix=64)
        test_par(prompt)