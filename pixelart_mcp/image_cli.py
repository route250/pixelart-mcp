import argparse
from typing import Literal
from pixelart_mcp.image_generator import generate_image, parse_size, MODEL_IDS

def to_pix( size ) -> Literal[32, 48, 64, 128, 256, 512]:
    """
    サイズをピクセルアート化サイズに変換するヘルパー関数
    """
    if size == "32":
        return 32
    elif size == "48":
        return 48
    elif size == "64":
        return 64
    elif size == "128":
        return 128
    elif size == "256":
        return 256
    elif size == "512":
        return 512
    else:
        raise ValueError(f"無効なピクセルアート化サイズ: {size}")

def main():
    parser = argparse.ArgumentParser(description="自然言語から画像を生成します")
    parser.add_argument("prompt", help="画像を生成するためのプロンプト（例: 'pixel sprite of a ninja cat')")

    parser.add_argument("-m", "--model", default="default", choices=MODEL_IDS.keys(), help=f"使用するモデルIDのキー (デフォルト: default). 利用可能なモデル: {', '.join(MODEL_IDS.keys())}")
    parser.add_argument("-n", "--num-steps", type=int, default=75, help="推論ステップ数 (デフォルト: 75)")

    parser.add_argument("-s", "--size", type=str, default="512x512", help="生成画像サイズ (WIDTHxHEIGHT, デフォルト: 512x512)")
    parser.add_argument("-r", "--resize", type=str, default=None, help="生成画像サイズ (WIDTHxHEIGHT, デフォルト: 512x512)")

    parser.add_argument("-p", "--pixel", choices=["off", "32", "48", "64", "128"], default="off", help="ピクセルアート化サイズ (off, 32, 48, 64, 128)")

    parser.add_argument("-o", "--output", default="output.png", help="出力ファイル名 (デフォルト: output.png)")

    args = parser.parse_args()

    # --pixelと--sizeの排他制御
    if args.pixel != "off" and args.size != "512x512":
        print("[ERROR] --pixelと--sizeは同時に指定できません。どちらか一方のみ指定してください。")
        exit(1)

    if args.pixel != "off":
        # ピクセルアート化
        pixel_art_mode = to_pix(args.pixel)
        generate_image(
            args.prompt,
            args.output,
            model_id_key=args.model,
            steps=args.num_steps,
            size=(512, 512),
            resize_to=None,
            pixel_art_mode=pixel_art_mode
        )
    else:
        # 通常画像生成
        size = parse_size(args.size)
        resize_to = parse_size(args.resize) if args.resize is not None else None
        generate_image(
            args.prompt,
            args.output,
            model_id_key=args.model,
            steps=args.num_steps,
            size=size,
            resize_to=resize_to,
            pixel_art_mode=None
        )

if __name__ == "__main__":
    main()
