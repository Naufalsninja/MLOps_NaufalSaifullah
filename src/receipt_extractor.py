import json, os, subprocess, base64, re
from pathlib import Path

IMAGE_PATH = Path("data/raw/nota-sample.png")
MODEL = os.environ.get("LM_STUDIO_MODEL", "qwen2.5-vl-7b-instruct")

# Encode gambar ke Base64
with open(IMAGE_PATH, "rb") as img_file:
    base64_image = base64.b64encode(img_file.read()).decode('utf-8')

payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Kamu adalah sistem OCR profesional. Analisis gambar nota/resi ini dengan teliti.\n"
                        "Ekstrak informasi berikut ke dalam format JSON murni tanpa markdown/backticks:\n"
                        "{\n"
                        '  "merchant": "Nama Toko/Restoran",\n'
                        '  "tanggal": "YYYY-MM-DD atau teks tanggal",\n'
                        '  "item": ["item 1", "item 2"],\n'
                        '  "subtotal": angka,\n'
                        '  "pajak": angka,\n'
                        '  "total": angka\n'
                        "}\n"
                        "Jika ada bidang yang tidak ditemukan atau tidak terbaca, gunakan null atau 0. Jangan mengarang."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    "temperature": 0.1
}

Path("temp_payload.json").write_text(json.dumps(payload), encoding="utf-8")

cmd = [
    "curl.exe", "-s", "-X", "POST", "http://localhost:1234/v1/chat/completions",
    "-H", "Content-Type: application/json",
    "-d", "@temp_payload.json"
]

print("Mengirim gambar ke LM Studio via curl.exe...")
res = subprocess.run(cmd, capture_output=True, text=True)

if Path("temp_payload.json").exists():
    Path("temp_payload.json").unlink()

try:
    response_data = json.loads(res.stdout)
    raw_content = response_data["choices"][0]["message"]["content"]

    # Bersihkan tag markdown ```json ... ```
    cleaned_content = re.sub(r"^```[a-zA-Z]*\n?", "", raw_content.strip())
    cleaned_content = re.sub(r"\n?```$", "", cleaned_content.strip())

    # Validasi bahwa output adalah JSON sah
    parsed_json = json.loads(cleaned_content)

    Path("reports").mkdir(exist_ok=True)
    Path("reports/receipt.json").write_text(json.dumps(parsed_json, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n--- HASIL EKSTRAKSI NOTA (BERSIH) ---")
    print(json.dumps(parsed_json, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error parsing response: {e}")
    print("Output mentah:", res.stdout)
