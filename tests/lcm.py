
from diffusers.schedulers.scheduling_lcm import LCMScheduler
from diffusers.pipelines.pixart_alpha.pipeline_pixart_alpha import PixArtAlphaPipeline
from diffusers.pipelines.pipeline_utils import DiffusionPipeline
from diffusers.pipelines.latent_consistency_models.pipeline_latent_consistency_text2img import LatentConsistencyModelPipeline
from diffusers.pipelines.stable_diffusion.pipeline_output import StableDiffusionPipelineOutput
from diffusers.models.transformers.transformer_2d import Transformer2DModel
from peft import PeftModel
import torch
from PIL.Image import Image

def testrun():
    pipe = DiffusionPipeline.from_pretrained(
        "SimianLuo/LCM_Dreamshaper_v7",
        torch_dtype=torch.float16,
        # variant="fp16",
        use_safetensors=True
        ).to(torch.device("mps"))
    assert isinstance(pipe, (LatentConsistencyModelPipeline, PixArtAlphaPipeline)), f"Expected LCM or PixArtAlphaPipeline, got {type(pipe)}"
    
    #pipe2 = pipe.to(torch_device="cuda", torch_dtype=torch.float16)
    prompt = "a cute cat in a sky"
    prompt = "“Photorealistic photo of a young professional businessman (early 30s, smart casual) sitting at a sleek office desk, intently focused on a laptop screen, brainstorming marketing strategy. Natural daylight streaming through large windows with city skyline in the background. On the desk: notes, charts, coffee cup, smartphone. Whiteboard behind with colorful growth graphs and sticky notes. Shot on Canon EOS R5 with 50mm f/1.8 lens, shallow depth of field, soft cinematic lighting, high resolution, ultra‑sharp focus.”"
    prompt = "A side-scrolling space shooter game background, deep outer space with stars, distant galaxies, colorful nebulae, asteroids floating, futuristic sci-fi feeling, parallax layers for scrolling, 16-bit pixel art style"
    # 画像を生成
    out = pipe(
        prompt=prompt, 
        width=512, height=512, 
        num_inference_steps=6, 
        guidance_scale=8, 
        lcm_origin_steps=50, 
        output_type="pil")
    if not isinstance(out, StableDiffusionPipelineOutput ):
        raise TypeError(f"Expected LatentConsistencyModelPipeline output, got {type(out)}")
    image = out.images[0]
    if not isinstance(image, Image):
        raise TypeError(f"Expected PIL Image, got {type(image)}")

    # 保存する画像のファイル名を設定
    file_name = f"image.png"
    # 画像をPNG形式でバイトIOオブジェクトに保存
    image.save(file_name, format="PNG")
    # 保存した画像のパスをリストに追加
    print(f"saved image: {file_name}")

def load_flash_pixart(device):
    # LoRA アダプタ付き Transformer
    transformer = Transformer2DModel.from_pretrained(
        "PixArt-alpha/PixArt-XL-2-1024-MS",
        subfolder="transformer",
        torch_dtype=torch.float16
    )
    transformer = PeftModel.from_pretrained(transformer, "jasperai/flash-pixart")
    pipe = PixArtAlphaPipeline.from_pretrained(
        "PixArt-alpha/PixArt-XL-2-1024-MS",
        transformer=transformer,
        torch_dtype=torch.float16
    )
    pipe.scheduler = LCMScheduler.from_pretrained(
        "PixArt-alpha/PixArt-XL-2-1024-MS",
        subfolder="scheduler",
        timestep_spacing="trailing"
    )
    return pipe.to(device)

def testrun_flash(model_type="flash", device=torch.device("mps")):
    if model_type == "flash":
        pipe = load_flash_pixart(device)
    else:
        pipe = DiffusionPipeline.from_pretrained(
            "SimianLuo/LCM_Dreamshaper_v7"
        ).to(device)

    assert isinstance(pipe, (LatentConsistencyModelPipeline, PixArtAlphaPipeline)), f"Expected LCM or PixArtAlphaPipeline, got {type(pipe)}"

    prompt = "Photorealistic young businessman in office, brainstorming on laptop"
    out = pipe(
        prompt=prompt,
        height=512,
        width=512,
        num_inference_steps=4,
        guidance_scale=7.5,
        lcm_origin_steps=50 if hasattr(pipe, "lcm_origin_steps") else None,
        output_type="pil"
    )
    assert isinstance(out, (StableDiffusionPipelineOutput, PixArtAlphaPipeline)), f"Expected LatentConsistencyModelPipeline or PixArtAlphaPipeline output, got {type(out)}"
    image = out.images[0]
    assert isinstance(image, Image), f"Expected PIL Image, got {type(image)}"
    image.save("out_flash_pixart.png")
    print("Saved out_flash_pixart.png")

if __name__ == "__main__":
    testrun()
    print("Test run completed successfully.")