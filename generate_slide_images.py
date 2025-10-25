import base64
import os
from pathlib import Path
from dotenv import load_dotenv
import time
from openai import OpenAI
from alternative_plan.image_from_prompt_requests import generate_image as fallback_generate_image

load_dotenv()

API_BASE_URL = "https://api.thucchien.ai"
API_KEY = os.getenv("THUCCHIEN_API_KEY")
if not API_KEY:
    raise RuntimeError("Thiếu biến THUCCHIEN_API_KEY trong môi trường hoặc file .env")
CLIENT = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

IMAGE_DETAILS = [
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. A vibrant and modern Vietnamese Tet background, rich with traditional elements. Include peach blossoms, kumquat trees, red lanterns, and lucky money envelopes. The overall atmosphere should convey a sense of family reunion and financial growth. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "tet_bg_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. An illustration depicting common financial worries during Tet, such as a pile of receipts, an empty wallet, or a person looking stressed about expenses. Use a relatable, slightly somber yet hopeful tone. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "tet_worry_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. A modern, abstract representation of a technological 'god of wealth' or a smart financial solution. Show money growing or being managed effortlessly through a digital interface, symbolizing automated profit. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "solution_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. An abstract illustration of significant financial growth. Depict an upward trending graph, stylized coins, and vibrant plant sprouts, symbolizing money effortlessly increasing over time, even during holidays. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "growth_chart_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. A happy, multi-generational Vietnamese family celebrating Tet. Parents and children are smiling, wearing traditional clothes (Ao Dai), and exchanging lucky money. Subtly integrate elements suggesting automatic financial management or saving, like a small, stylized digital interface in the background showing automated deposits, emphasizing financial peace of mind through effortless saving. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "happy_family_tet.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. A symbolic image representing future financial goals and stability. Illustrate a young seedling growing into a strong, mature tree against a backdrop of a bright, prosperous future or a modern cityscape at sunrise. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "future_goals_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. An artistic representation of 'Sowing Seeds of Prosperity, Reaping Joyful Peace' (Gieo Mầm Tài Lộc, Gặt Hái An Vui). Show a hand gently sowing glowing seeds that transform into money-shaped blossoms on a vibrant plant, surrounded by a serene family scene. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "big_idea_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. An illustration showing various digital and traditional communication channels converging. Include icons for social media (Facebook, TikTok, YouTube), a mobile phone with a banking app, and a physical branch building, symbolizing integrated marketing. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "multichannel_placeholder.png"
    },
    {
        "prompt": "A realistic, bright, and festive Tet atmosphere. A three-generation Vietnamese family making Banh Chung together in a cozy courtyard during Tet. In the corner of the garden, a vibrant yellow apricot blossom tree is in full bloom. Beneath the tree, a glowing 3D graphic of a 'lucky sprout' is strongly growing, emitting a warm golden light. The scene should feel modern yet traditional. No text, realistic, bright, festive Tet atmosphere.",
        "output_filename": "tet_mockup_family.png"
    },
    {
        "prompt": "A minimalist design of a QR code. The QR code should be prominent, with a subtle, integrated Techcombank logo at its center. The background is clean and inviting. No text, just the QR code and subtle branding.",
        "output_filename": "qr_code_placeholder.png"
    }
]

OUTPUT_DIR = Path("presentation/slides/img")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for i, detail in enumerate(IMAGE_DETAILS):
    print(f"Generating image {i+1}/{len(IMAGE_DETAILS)}: {detail['output_filename']}")
    output_path = OUTPUT_DIR / detail["output_filename"]
    
    try:
        result = CLIENT.images.generate(
            model="imagen-4",
            prompt=detail["prompt"],
            n=1,
        )
        image_b64 = result.data[0].b64_json
        output_path.write_bytes(base64.b64decode(image_b64))
        print(f"Đã lưu ảnh sinh từ prompt tại: {output_path}")
        time.sleep(1) # Add a delay to avoid hitting API rate limits
    except Exception as e:
        print(f"Lỗi khi tạo ảnh {detail['output_filename']} bằng phương thức chính: {e}. Thử phương án phụ...")
        try:
            image_bytes = fallback_generate_image(detail["prompt"])
            output_path.write_bytes(image_bytes)
            print(f"Đã lưu ảnh sinh từ phương án phụ tại: {output_path}")
            time.sleep(1) # Add a delay to avoid hitting API rate limits
        except Exception as fallback_e:
            print(f"Lỗi khi tạo ảnh {detail['output_filename']} bằng phương án phụ: {fallback_e}")
