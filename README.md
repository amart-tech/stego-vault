# StegoVault: Dual-Layer Image Steganography with AES-128 Encryption

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-green.svg)](https://flask.palletsprojects.com/)
[![Cryptography](https://img.shields.io/badge/Security-AES--128--CBC%20%7C%20HMAC--SHA256-indigo.svg)](https://cryptography.io/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**StegoVault** is a full-stack security application providing **Dual-Layer Information Hiding**. It combines authenticated symmetric cryptography (AES-128-CBC + HMAC-SHA256) with Spatial Domain Least Significant Bit (LSB) Steganography in RGB images.

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Mathematical & Algorithmic Formulation](#-mathematical--algorithmic-formulation)
- [Project Structure](#-project-structure)
- [Installation & Quickstart](#-installation--quickstart)
- [API Reference](#-api-reference)
- [Security Specifications](#-security-specifications)
- [Author & Acknowledgments](#-author--acknowledgments)

---

## 🌟 Key Features

1. **Dual-Layer Security Architecture**:
   - **Layer 1 (Cryptography):** Plaintext is encrypted into ciphertext using AES-128-CBC with PKCS7 padding and authenticated via HMAC-SHA256. Cryptographic keys are derived from a user passphrase using `PBKDF2HMAC` (SHA-256, 480,000 iterations, 16-byte random salt).
   - **Layer 2 (Concealment):** The encrypted payload (salt + ciphertext) is concealed in the least significant bits of an image's Red, Green, and Blue channels.
2. **Objective Quality Benchmarking (PSNR & MSE)**:
   - Real-time computation of **Peak Signal-to-Noise Ratio (PSNR)** and **Mean Squared Error (MSE)** upon embedding. Typical PSNR values exceed **65 dB**, mathematically proving visual imperceptibility.
3. **Collision-Proof 32-Bit Length Header**:
   - Prepend a 32-bit (4-byte) big-endian unsigned integer storing the exact byte length of the payload. Eliminates delimiter collision flaws inherent in sentinel markers (`###END###`).
4. **Flexible Carrier Ingestion**:
   - Supports both **PNG** and **JPEG/JPG** carrier images. Encoded outputs are saved as lossless PNG to guarantee byte-exact pixel retention.
5. **Memory-Safe Architecture**:
   - In-memory image processing using Python's `io.BytesIO` and Base64 streaming. Zero temporary files are written to disk.
6. **Modern Responsive UI**:
   - Single-page application (SPA) featuring real-time capacity meters, drag-and-drop zones, password visibility toggles, clipboard copy, and toast notifications.

---

## 🏛️ System Architecture

```
[Plaintext Secret Message]
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: CRYPTOGRAPHIC ENCRYPTION (Fernet / PBKDF2)             │
│  • Salt: 16 cryptographically random bytes (os.urandom)         │
│  • KDF: PBKDF2-HMAC-SHA256 (480,000 iterations)                 │
│  • Cipher: AES-128 in CBC mode + PKCS7 padding                  │
│  • MAC: HMAC-SHA256 authenticated envelope                      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
                     [Payload: Salt + Ciphertext]
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: SPATIAL LSB EMBEDDING                                 │
│  • Length Header: 32-bit big-endian unsigned integer (4 bytes)  │
│  • Bitstream: [32-bit Header] + [Payload Bits]                  │
│  • Carrier Channels: Red, Green, Blue (1 bit per channel)       │
│  • Bitwise Injection: channel = (channel & ~1) | bit            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
             [Lossless Steganographic PNG Output]
```

---

## 📐 Mathematical & Algorithmic Formulation

### 1. Spatial Bitwise Operations
For an 8-bit color channel $C \in [0, 255]$ and a secret bit $b \in \{0, 1\}$:

* **Clear LSB to 0:**
  $$C_{\text{cleared}} = C \ \& \ \sim 1 \quad \equiv \quad C \ \& \ 254$$
* **Inject Secret Bit:**
  $$C_{\text{stego}} = C_{\text{cleared}} \ | \ b$$
* **Extract Secret Bit:**
  $$b = C_{\text{stego}} \ \& \ 1$$
* **Byte Assembly (Decoder):**
  $$A_{k} = (A_{k-1} \ll 1) \ | \ b$$

### 2. Distortion Metrics (PSNR & MSE)
For an $M \times N$ image with 3 color channels ($K = 3MN$ channel values):

* **Mean Squared Error (MSE):**
  $$\text{MSE} = \frac{1}{K} \sum_{i=1}^{K} \left( C_{\text{original}}(i) - C_{\text{stego}}(i) \right)^2$$
* **Peak Signal-to-Noise Ratio (PSNR):**
  $$\text{PSNR} = 10 \cdot \log_{10} \left( \frac{255^2}{\text{MSE}} \right) \quad (\text{dB})$$
  *(A PSNR value $> 50\text{ dB}$ confirms that deviations are imperceptible to human visual perception).*

---

## 📁 Project Structure

```
stego_vault/
├── app.py                  # Flask server, routing, in-memory stream processing
├── steganography.py        # Core cryptography (AES/PBKDF2) and LSB engine
├── requirements.txt        # Pinned dependencies (Flask, Pillow, cryptography, gunicorn)
├── Procfile                # Production deployment configuration
├── static/
│   ├── css/
│   │   └── style.css       # Responsive dark theme styling
│   └── js/
│       └── main.js         # Single-page controller, capacity estimation, AJAX
└── templates/
    └── index.html          # Semantic HTML5 user interface
```

---

## 🚀 Installation & Quickstart

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 1. Clone or Extract the Project
```bash
cd stego_vault
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Development Server
```bash
python app.py
```
Server runs at: `http://127.0.0.1:5001` (Port 5001 is preconfigured to prevent conflicts with macOS AirPlay).

---

## 🔌 API Reference

### `POST /api/analyze`
Analyzes a carrier image and returns capacity metrics before encoding.
- **Payload:** `multipart/form-data` with `image` (PNG, JPG, or JPEG).
- **Response:**
  ```json
  {
    "success": true,
    "capacity": {
      "width": 1920,
      "height": 1080,
      "total_pixels": 2073600,
      "total_available_bits": 6220800,
      "usable_bits": 6220768,
      "max_payload_bytes": 777596
    }
  }
  ```

### `POST /api/encode`
Encrypts a message and embeds it into the carrier image.
- **Payload:** `multipart/form-data` with `image`, `message`, `passphrase`.
- **Response:**
  ```json
  {
    "success": true,
    "filename": "stego_vault_encoded.png",
    "image_data": "data:image/png;base64,...",
    "stats": {
      "payload_length_bytes": 180,
      "salt_size_bytes": 16,
      "ciphertext_size_bytes": 164,
      "total_bits_embedded": 1472,
      "capacity_used_percent": 0.0237,
      "mse": 0.000236,
      "psnr_db": 84.4
    }
  }
  ```

### `POST /api/decode`
Extracts and decrypts a hidden payload from an encoded stego image.
- **Payload:** `multipart/form-data` with `image` (PNG only) and `passphrase`.
- **Response:**
  ```json
  {
    "success": true,
    "message": "Decrypted secret message content here",
    "stats": {
      "payload_length_bytes": 180,
      "salt_size_bytes": 16,
      "ciphertext_size_bytes": 164,
      "total_bits_extracted": 1472
    }
  }
  ```

---

## 🔒 Security Specifications

* **Why Lossless PNG is Required for Stego Output**:  
  Lossy formats like JPEG apply Discrete Cosine Transform (DCT) and Quantization, which discards high frequencies and approximates pixel values on decompression. This obliterates spatial LSB modifications ($\pm 1$). PNG uses lossless DEFLATE (LZ77 + Huffman), preserving every pixel value bit-for-bit.
* **Why Delimiter Collisions are Avoided**:  
  Encrypted ciphertext is indistinguishable from random bytes. A fixed 32-bit big-endian length prefix header guarantees that the decoder extracts the exact payload length without relying on sentinel strings that could accidentally appear inside ciphertext.

---

## 👤 Author & Acknowledgments

- **Developer:** Amartya Bhushan
- **Technologies:** Python 3, Flask, Pillow (PIL), Cryptography (Fernet / PBKDF2), HTML5, CSS3, JavaScript (ES6).
