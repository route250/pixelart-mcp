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


def test_s1():

        prompt='white cat, walking, side view'
        outpath='tmp/output-test-s1.png'
        generate_image(
            prompt,
            outpath,
            model_id_key='s1',
            #steps=10,
        )

def test_s2():

        prompt='white cat, walking, blue sky'
        outpath='tmp/output-test-s2.png'
        generate_image(
            prompt,
            outpath,
            model_id_key='s2',
        )

def test_pix( *, pix:Literal[32,48,64,128,256,512]=128, steps:int=50):

        prompt='Godzilla'
        outpath=f'tmp/output-test-pix{pix}.png'
        generate_image(
            prompt,
            outpath,
            steps=steps,
            pixel_art_mode=pix,
        )

def test3():

        prompt='white cat, walking, side view'
        prompt='Godzilla'
        outpath='tmp/output-test-3.png'
        generate_image(
            prompt,
            outpath,
            model_id_key='par',
            steps=50,
            pixel_art_mode=64,
        )

if __name__ == "__main__":
        test_s1()
        test_s2()
        test_pix( pix=512)
        test_pix( pix=64)