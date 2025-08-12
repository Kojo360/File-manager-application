import os
import time
import shutil
import re
import logging
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from django.conf import settings

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# === Directory Configuration ===
# Use absolute paths for all output directories at the project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
SCAN_DIR            = os.path.join(BASE_DIR, "incoming-scan")
FULLY_INDEXED_DIR   = os.path.join(BASE_DIR, "fully_indexed")
PARTIAL_INDEXED_DIR = os.path.join(BASE_DIR, "partially_indexed")
FAILED_DIR          = os.path.join(BASE_DIR, "failed")

# Ensure required directories exist
for d in (SCAN_DIR, FULLY_INDEXED_DIR, PARTIAL_INDEXED_DIR, FAILED_DIR):
    os.makedirs(d, exist_ok=True)

# === OCR Configuration ===
# Auto-detect tesseract installation
import subprocess
import sys
import shutil

def get_tesseract_path():
    """Auto-detect tesseract installation"""
    # For Render/Linux environments with apt.txt, tesseract will be in /usr/bin
    linux_paths = [
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract'
    ]
    
    for path in linux_paths:
        if os.path.exists(path):
            logging.info(f"Found tesseract at: {path}")
            return path
    
    # Then try system PATH (works for both Linux and Windows)
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        logging.info(f"Found tesseract in PATH: {tesseract_path}")
        return tesseract_path
    
    # Common installation paths for different platforms
    common_paths = [
        '/usr/bin/tesseract',  # Linux (Docker)
        '/usr/local/bin/tesseract',  # Linux alternative
        r"C:\Users\KC-User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",  # Windows
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows alternative
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # If nothing found, return default command and let system handle it
    return 'tesseract'

def get_poppler_path():
    """Auto-detect poppler installation"""
    # For Render/Linux with apt.txt, poppler utilities will be in PATH
    if shutil.which('pdftoppm'):
        logging.info("Found poppler utilities in system PATH")
        return None  # Use system PATH
    
    # Windows fallback
    windows_poppler = r"C:\poppler-24.08.0\Library\bin"
    if os.path.exists(windows_poppler):
        return windows_poppler
    
    return None  # Use system PATH

# Configure paths
TESSERACT_CMD = get_tesseract_path()
POPPLER_PATH = get_poppler_path()

# Set pytesseract command - ensure it's set properly
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    logging.info(f"[Tesseract] Configured: {TESSERACT_CMD}")
else:
    # Fallback to default command
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'
    logging.warning("[Tesseract] Path not found, using default 'tesseract' command")

logging.info(f"[Tesseract] Final command: {pytesseract.pytesseract.tesseract_cmd}")
logging.info(f"[Poppler] Path: {POPPLER_PATH or 'System PATH'}")

# Verify tesseract is working - this is what we need to see in logs
try:
    import subprocess
    result = subprocess.run([pytesseract.pytesseract.tesseract_cmd, '--version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version = result.stdout.split('\n')[0] if result.stdout else 'Unknown'
        logging.info(f"[Tesseract] {version}")
    else:
        logging.error(f"[Tesseract] Verification error: {result.stderr}")
except FileNotFoundError as e:
    logging.error(f"[Tesseract] Verification error: {e}")
except Exception as e:
    logging.error(f"[Tesseract] Verification error: {e}")

# === OCR and File Routing Logic ===
def extract_text(path):
    """Extract text from PDF or image files using OCR"""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            # Use poppler to convert PDF to images, then OCR
            if POPPLER_PATH:
                pages = convert_from_path(path, poppler_path=POPPLER_PATH)
            else:
                pages = convert_from_path(path)  # Use system PATH
            return "".join(pytesseract.image_to_string(p) for p in pages)
        else:
            # Direct OCR on image files
            img = Image.open(path).convert("RGB")
            return pytesseract.image_to_string(img)
    except Exception as e:
        logging.error(f"OCR extraction failed for {path}: {e}")
        raise  # Re-raise to let caller handle the error

def parse_fields(text):
    m_name = re.search(r"name\s*:\s*([A-Za-z ]+)", text, re.IGNORECASE)
    m_account = re.search(r"account\s*no\s*[:\-]?\s*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
    name = m_name.group(1).strip().replace(" ", "_") if m_name else None
    account = m_account.group(1).strip() if m_account else None
    return name, account

def route_file(src_path):
    if not os.path.exists(src_path):
        logging.error(f"Source file not found: {src_path}")
        return None
    filename = os.path.basename(src_path)
    ext = os.path.splitext(filename)[1].lower()
    text = extract_text(src_path)
    name, account = parse_fields(text)
    is_image = ext in [".png", ".jpg", ".jpeg"]
    if name and account:
        new_filename = f"{name}_{account}.pdf" if is_image else f"{name}_{account}{ext}"
        dest_dir = FULLY_INDEXED_DIR
    elif name or account:
        key = name or account
        new_filename = f"{key}.pdf" if is_image else f"{key}{ext}"
        dest_dir = PARTIAL_INDEXED_DIR
    else:
        new_filename = filename
        dest_dir = FAILED_DIR
    dest_path = os.path.join(dest_dir, new_filename)
    base, extn = os.path.splitext(new_filename)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_dir, f"{base}_{counter}{extn}")
        counter += 1
    try:
        if dest_dir == FAILED_DIR:
            shutil.move(src_path, dest_path)
            logging.info(f"[FAILED] {filename} → {new_filename}")
            return dest_path
        if is_image:
            img = Image.open(src_path).convert("RGB")
            img.save(dest_path, "PDF", resolution=100.0)
            os.remove(src_path)
            logging.info(f"[FULLY_INDEXED] {filename} → {new_filename} (image → PDF)")
            return dest_path
        else:
            shutil.move(src_path, dest_path)
            logging.info(f"[FULLY_INDEXED] {filename} → {new_filename}")
            return dest_path
    except Exception as e:
        logging.error(f"Failed to route file {filename}: {e}")
        if os.path.exists(src_path):
            shutil.move(src_path, os.path.join(FAILED_DIR, filename))
        return None

class ScanHandler(FileSystemEventHandler):
    _lock = threading.Lock()
    _timer = None
    def _delayed_batch_process(self):
        with self._lock:
            ScanHandler._timer = None
        time.sleep(5)
        for fname in os.listdir(SCAN_DIR):
            if not fname.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                continue
            fpath = os.path.join(SCAN_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            last_exception = None
            for _ in range(10):
                try:
                    with open(fpath, 'rb') as f:
                        f.read(1)
                    route_file(fpath)
                    break
                except Exception as e:
                    last_exception = e
                    time.sleep(0.5)
            else:
                logging.error(f"Failed to process {fpath}: {last_exception}")
    def _schedule_batch(self):
        with self._lock:
            if ScanHandler._timer:
                ScanHandler._timer.cancel()
            ScanHandler._timer = threading.Timer(0.5, self._delayed_batch_process)
            ScanHandler._timer.start()
    def on_created(self, event):
        if not event.is_directory:
            self._schedule_batch()
    def on_moved(self, event):
        if not event.is_directory:
            self._schedule_batch()
    def on_modified(self, event):
        pass

def start_watcher():
    logging.info(f"[WATCHING] {SCAN_DIR} → (fully|partial|failed)")
    observer = Observer()
    observer.schedule(ScanHandler(), path=SCAN_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
