"""
Flask Application for StegoVault
Handles routes, image upload validation, in-memory stream processing, and API responses.
"""

import base64
import os
import zipfile
from io import BytesIO

from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, UnidentifiedImageError

from steganography import (
    encode_lsb,
    decode_lsb,
    calculate_capacity,
    StegoSecurityError,
    SALT_SIZE_BYTES,
    PBKDF2_ITERATIONS,
)

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, "templates"),
    static_folder=os.path.join(base_dir, "static"),
)

# 16 MB max upload limit
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "success": False,
        "error": "File size exceeds the 16MB maximum limit. Please upload a smaller image.",
    }), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Route not found."}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error."}), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download-source")
def download_source():
    """Serves the project ZIP archive."""
    prebuilt = os.path.join(os.path.dirname(base_dir), "stego_vault.zip")
    if os.path.exists(prebuilt):
        return send_file(
            prebuilt,
            mimetype="application/zip",
            as_attachment=True,
            download_name="stego_vault.zip",
        )

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__",) and not d.startswith(".")]
            for fname in files:
                if fname.endswith((".pyc", ".DS_Store")) or fname == "stego_vault.zip":
                    continue
                full = os.path.join(root, fname)
                arc = os.path.relpath(full, os.path.dirname(base_dir))
                zf.write(full, arc)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name="stego_vault.zip",
    )


@app.route("/api/analyze", methods=["POST"])
def analyze_image():
    """Analyzes carrier image dimensions and returns usable capacity metrics."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400

    file = request.files["image"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No image selected."}), 400

    allowed_exts = (".png", ".jpg", ".jpeg")
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_exts):
        return jsonify({
            "success": False,
            "error": "Only PNG, JPG, and JPEG images are supported for carrier analysis.",
        }), 400

    try:
        img_bytes = file.read()
        image = Image.open(BytesIO(img_bytes))

        if image.format not in ("PNG", "JPEG", "JPG"):
            return jsonify({
                "success": False,
                "error": f"Image format '{image.format}' is not supported. Please upload a valid PNG or JPEG image.",
            }), 400

        capacity = calculate_capacity(image)
        return jsonify({"success": True, "capacity": capacity})

    except UnidentifiedImageError:
        return jsonify({"success": False, "error": "Uploaded file is not a valid image."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Error analysing image: {str(e)}"}), 500


@app.route("/api/encode", methods=["POST"])
def encode_route():
    """Encodes secret message into carrier image and returns Base64 PNG."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Please select a carrier PNG or JPEG image."}), 400

    file = request.files["image"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No image file chosen."}), 400

    allowed_exts = (".png", ".jpg", ".jpeg")
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_exts):
        return jsonify({
            "success": False,
            "error": "Unsupported carrier format. Please upload a PNG or JPEG carrier image.",
        }), 400

    secret_message = request.form.get("message", "").strip()
    passphrase = request.form.get("passphrase", "").strip()

    if not secret_message:
        return jsonify({"success": False, "error": "Secret message cannot be empty."}), 400
    if not passphrase:
        return jsonify({"success": False, "error": "Encryption passphrase cannot be empty."}), 400

    try:
        file_bytes = file.read()
        image = Image.open(BytesIO(file_bytes))

        if image.format not in ("PNG", "JPEG", "JPG"):
            return jsonify({
                "success": False,
                "error": f"Uploaded file format '{image.format}' is not supported. Please upload a valid PNG or JPEG image.",
            }), 400

        stego_image, stats = encode_lsb(image, secret_message, passphrase)

        output_buf = BytesIO()
        stego_image.save(output_buf, format="PNG")
        output_buf.seek(0)
        encoded_b64 = base64.b64encode(output_buf.getvalue()).decode("utf-8")
        data_url = f"data:image/png;base64,{encoded_b64}"

        return jsonify({
            "success": True,
            "filename": "stego_vault_encoded.png",
            "image_data": data_url,
            "stats": stats,
            "crypto_info": {
                "cipher": "AES-128-CBC with PKCS7 padding",
                "kdf": f"PBKDF2-HMAC-SHA256 ({PBKDF2_ITERATIONS:,} rounds)",
                "salt_bytes": SALT_SIZE_BYTES,
                "mac": "HMAC-SHA256 authenticated",
            },
        })

    except StegoSecurityError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except UnidentifiedImageError:
        return jsonify({"success": False, "error": "Uploaded file is not a valid image."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/api/decode", methods=["POST"])
def decode_route():
    """Extracts and decrypts secret message from stego PNG."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Please upload an encoded PNG image."}), 400

    file = request.files["image"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "No image file chosen."}), 400

    filename = file.filename.lower()
    if not filename.endswith(".png"):
        return jsonify({
            "success": False,
            "error": (
                "Invalid stego image format. Stego images must be in lossless PNG format. "
                "JPEG images cannot be decoded because lossy compression (DCT & quantization) "
                "permanently destroys spatial LSB bits upon saving."
            ),
        }), 400

    passphrase = request.form.get("passphrase", "").strip()
    if not passphrase:
        return jsonify({"success": False, "error": "Please provide the decryption passphrase."}), 400

    try:
        file_bytes = file.read()
        image = Image.open(BytesIO(file_bytes))

        if image.format != "PNG":
            return jsonify({
                "success": False,
                "error": "Uploaded file does not have a valid PNG internal signature.",
            }), 400

        plaintext, stats = decode_lsb(image, passphrase)

        return jsonify({"success": True, "message": plaintext, "stats": stats})

    except StegoSecurityError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except UnidentifiedImageError:
        return jsonify({"success": False, "error": "Uploaded file is not a valid image."}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\nStegoVault server running at http://127.0.0.1:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
