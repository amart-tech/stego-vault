# StegoVault: Viva Defense & Presentation Guide

This guide contains everything you need to deliver an outstanding presentation and ace your viva examination.

---

## 📑 5-Minute Presentation Outline (5 Slides)

### Slide 1: Title & Problem Statement
* **Title:** Dual-Layer Image Steganography with Authenticated AES Encryption (StegoVault)
* **Presenter:** Amartya Bhushan
* **The Problem:**
  - Standard encryption protects content, but raw ciphertext draws immediate suspicion from network monitors.
  - Standard LSB steganography conceals existence, but stores plaintext—if discovered, the secret is completely exposed.
  - Conventional implementations use delimiters like `###END###` which cause **Delimiter Collisions** with encrypted bytes.

### Slide 2: Proposed Dual-Layer Architecture
* **Layer 1 (Cryptography):**
  - Symmetric Cipher: AES-128 in CBC mode with PKCS7 padding.
  - Key Derivation: PBKDF2-HMAC-SHA256 with 480,000 iterations and a random 16-byte salt (`os.urandom`).
  - Integrity: HMAC-SHA256 signature ensures tamper resistance.
* **Layer 2 (Concealment):**
  - Protocol: 32-bit big-endian unsigned length header (collision-proof).
  - Spatial RGB LSB substitution across 3 color channels.
  - Zero disk clutter: 100% in-memory streaming using Python `io.BytesIO`.

### Slide 3: Mathematical Formulation & Bitwise Mechanics
* **Bit Extraction:** `bit = (byte >> (7 - i)) & 1`
* **LSB Clearing:** `cleared = channel & ~1` (masks with `0xFE` / `254`)
* **Bit Injection:** `stego_pixel = cleared | bit`
* **Byte Reassembly:** `accumulator = (accumulator << 1) | bit`
* **Objective Quality Metric (PSNR):**
  $$\text{MSE} = \frac{1}{K} \sum (C_{\text{orig}} - C_{\text{stego}})^2, \quad \text{PSNR} = 10 \cdot \log_{10}\left(\frac{255^2}{\text{MSE}}\right)$$

### Slide 4: Key Results & Empirical Evaluation
* **Visual Quality:** PSNR benchmark exceeds **65–78 dB** (well above the human imperceptibility threshold of 50 dB).
* **Format Resilience:**
  - PNG (Lossless): 100% bit preservation.
  - JPEG (Lossy): 0% survival due to DCT quantization tables.
  - Supported: Carrier inputs in both PNG & JPG (auto-exported as lossless PNG).

### Slide 5: Conclusion & Future Scope
* **Conclusion:** Successfully designed a defense-in-depth security tool that eliminates delimiter collisions, ensures visual imperceptibility, and prevents unauthorized decryption.
* **Future Scope (Major Project Roadmap):**
  - Pseudorandom pixel scattering via Chaotic Maps (Arnold's Cat Map / PRNG) to defeat Chi-Square steganalysis.
  - Frequency-domain transform (DCT) steganography for JPEG survival.
  - Audio steganography support for uncompressed `.wav` files.

---

## 🎬 2-Minute Live Demo Checklist

1. **Terminal:** Start server: `python app.py` (runs on `http://127.0.0.1:5001`).
2. **Encode Step:**
   - Drag & drop a carrier photo (PNG or JPG).
   - Point out the real-time capacity bar.
   - Enter secret message & passphrase.
   - Click **"Encrypt & Conceal in LSB"**.
   - Point to the telemetry output: **PSNR Quality (>65 dB)**, **HMAC-SHA256 Authenticated**, and **32-Bit Header**.
   - Click **"Download Stego PNG"**.
3. **Decode Step (Negative Test First - Shows Maturity!):**
   - Switch to **"Decode / Reveal Message"** tab.
   - Drag & drop the downloaded stego PNG.
   - Type a **wrong passphrase** -> Click Extract -> Show the red error toast: *"Decryption failed: Incorrect passphrase or stego-data corrupted."*
   - Explain: *"The HMAC signature immediately caught the invalid key."*
4. **Decode Step (Positive Test):**
   - Enter the **correct passphrase** -> Click Extract.
   - The original secret text appears instantly in the terminal display.
   - Click **"Copy"** to demonstrate clipboard integration.

---

## 🎯 Top 10 Viva Questions & Winning Answers

#### Q1: "Why did you combine Cryptography with Steganography?"
> **Answer:** *"Cryptography conceals the meaning of a message, but ciphertext looks like encrypted noise and draws suspicion. Steganography conceals the very existence of communication inside harmless media. Combining both creates defense-in-depth: even if statistical steganalysis detects hidden data, the attacker only gets AES-128 ciphertext that cannot be decrypted without the passphrase."*

#### Q2: "Why can't you save the stego image as a JPEG?"
> **Answer:** *"JPEG uses lossy compression: it breaks images into $8 \times 8$ blocks, runs Discrete Cosine Transform (DCT), and applies Quantization (dividing and rounding high frequencies to save space). On decompression, pixel values are approximate and shift by $\pm 5$ to $\pm 15$. That rounding obliterates spatial LSB modifications ($\pm 1$). PNG uses DEFLATE (LZ77 + Huffman), which is 100% lossless and retains every bit exactly."*

#### Q3: "What is a Delimiter Collision, and how did you prevent it?"
> **Answer:** *"Most basic projects put a sentinel string like `###END###` at the end of the text. However, encrypted ciphertext looks like random binary noise and can accidentally contain the bytes of the delimiter. If that happens, the decoder stops prematurely (a Delimiter Collision) and corrupts the data. I solved this by writing a 32-bit big-endian unsigned integer at the first 32 channels storing the exact payload length."*

#### Q4: "Why use PBKDF2 with 480,000 iterations instead of simple SHA-256?"
> **Answer:** *"A single SHA-256 hash can be computed billions of times per second on GPUs, making brute-force dictionary attacks easy. PBKDF2 runs HMAC-SHA256 in a loop 480,000 times (the OWASP standard) with a 16-byte random salt. This computational cost makes GPU-accelerated brute forcing infeasible, and the salt prevents precomputed rainbow-table attacks."*

#### Q5: "What is PSNR and what does your score mean?"
> **Answer:** *"PSNR (Peak Signal-to-Noise Ratio) measures the ratio between maximum signal power ($255^2$) and corrupting noise (Mean Squared Error). In image processing, any PSNR above 50 dB is visually indistinguishable to human eyes. Our stego images achieve between 65 dB and 78 dB, mathematically proving zero visible distortion."*

#### Q6: "What mode of AES did you use, and why?"
> **Answer:** *"I used AES in CBC (Cipher Block Chaining) mode with PKCS7 padding, encapsulated within the Fernet specification. CBC mode ensures that repeating plaintext patterns produce different ciphertext blocks through IV chaining, and HMAC-SHA256 validates data integrity before decryption."*

#### Q7: "What is the maximum capacity of an image in your system?"
> **Answer:** *"Each pixel has 3 color channels (Red, Green, Blue), providing 3 bits per pixel. For an image of width $W$ and height $H$, the total available bits are $W \times H \times 3$. Reserving 32 bits for the length header, the maximum payload bytes are $\lfloor(W \times H \times 3 - 32) / 8\rfloor$. For example, a $1920 \times 1080$ image holds over 777 Kilobytes of encrypted payload."*

#### Q8: "How do you handle memory and temporary files?"
> **Answer:** *"All image reads, manipulations, and transmissions use Python's in-memory `io.BytesIO` buffers and Base64 Data URLs. No temporary files are ever written to the host server disk, preventing disk clutter and eliminating forensic data leakage."*

#### Q9: "Is this system vulnerable to Chi-Square steganalysis?"
> **Answer:** *"Yes, because bits are embedded sequentially from the first pixel, statistical tools like Chi-Square analysis can detect an anomaly in the LSB distribution at the start of the file. However, that is the exact reason for the dual-layer architecture: even when detected, the payload is impenetrable AES-128 ciphertext. In my future scope for the major project, I plan to add PRNG-based pixel scattering to defeat Chi-Square analysis."*

#### Q10: "Can you write the bitwise formulas on the board?"
> **Answer:** Write these 4 lines:
> 1. `bit = (byte >> (7 - i)) & 1`  *(Extract $i$-th bit)*
> 2. `cleared = channel & ~1`  *(Clear LSB to 0 using `0xFE` / `254`)*
> 3. `stego = cleared | bit`  *(Inject secret bit)*
> 4. `byte = (byte << 1) | bit`  *(Rebuild byte in decoder)*
