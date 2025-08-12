import os
import time
import shutil
import re
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === Directories ===

# Use absolute paths for all output directories at the project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
SCAN_DIR            = os.path.join(BASE_DIR, "incoming-scan")
FULLY_INDEXED_DIR   = os.path.join(BASE_DIR, "fully_indexed")
PARTIAL_INDEXED_DIR = os.path.join(BASE_DIR, "partially_indexed")
FAILED_DIR          = os.path.join(BASE_DIR, "failed")

# Make sure these exist
for d in (FULLY_INDEXED_DIR, PARTIAL_INDEXED_DIR, FAILED_DIR):
    os.makedirs(d, exist_ok=True)

# === OCR Tools ===
# Auto-detect tesseract and poppler installations
import subprocess
import platform
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
            print(f"[OCR CONFIG] Found tesseract at: {path}")
            return path
    
    # Then try system PATH (works for both Linux and Windows)
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        print(f"[OCR CONFIG] Found tesseract in PATH: {tesseract_path}")
        return tesseract_path
    
    # Platform-specific fallbacks
    if platform.system() == "Windows":
        common_paths = [
            r"C:\Users\KC-User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        ]
    else:
        common_paths = [
            '/usr/bin/tesseract',  # Linux (Docker)
            '/usr/local/bin/tesseract',  # Linux alternative
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
        print("[OCR CONFIG] Found poppler utilities in system PATH")
        return None  # Use system PATH
    
    # Windows fallback
    if platform.system() == "Windows":
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
    print(f"[OCR CONFIG] Tesseract configured: {TESSERACT_CMD}")
else:
    # Fallback to default command
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'
    print(f"[OCR CONFIG] Tesseract path not found, using default 'tesseract' command")

print(f"[OCR CONFIG] Tesseract: {TESSERACT_CMD}")
print(f"[OCR CONFIG] Poppler: {POPPLER_PATH or 'System PATH'}")

# Verify tesseract is working
try:
    result = subprocess.run([pytesseract.pytesseract.tesseract_cmd, '--version'], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"[OCR CONFIG] Tesseract verification successful: {result.stdout.split()[1] if result.stdout else 'Unknown version'}")
    else:
        print(f"[OCR CONFIG] Tesseract verification failed: {result.stderr}")
except Exception as e:
    print(f"[OCR CONFIG] Tesseract verification error: {e}")

# === Helpers ===

def extract_text(path):
    """Extract text from PDF or image files using OCR"""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            try:
                if POPPLER_PATH:
                    pages = convert_from_path(path, poppler_path=POPPLER_PATH)
                else:
                    pages = convert_from_path(path)  # Use system poppler
            except Exception as e:
                print(f"[ERROR] PDF conversion failed for {path}: {e}")
                raise  # Re-raise to let caller handle the error
            text = "".join(pytesseract.image_to_string(p) for p in pages)
        else:
            img = Image.open(path).convert("RGB")
            text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"[ERROR] OCR extraction failed for {path}: {e}")
        raise  # Re-raise to let caller handle the error

def parse_fields(text):
    # Extract individual name components from various possible fields
    patterns_name = [
        r"name\s*of\s*account\s*holder\s*\([^)]+\)\s*[:\-]?\s*([A-Za-z ]+?)(?:\s*\n|\s*Address|\s*Account|\s*DOB|\s*Occupation|$)",
        r"surname\s*[:\-]?\s*([A-Za-z ]+?)(?:\s*\n|\s*Address|\s*Account|\s*DOB|\s*Occupation|$)",
        r"first\s*name\s*[:\-]?\s*([A-Za-z ]+?)(?:\s*\n|\s*Address|\s*Account|\s*DOB|\s*Occupation|$)",
        r"other\s*names?\s*[:\-]?\s*([A-Za-z ]+?)(?:\s*\n|\s*Address|\s*Account|\s*DOB|\s*Occupation|$)",
        r"account\s*name\s*[:\-]?\s*([A-Za-z ]+?)(?:\s*\n|\s*Address|\s*Account|\s*DOB|\s*Occupation|$)",
        r"print\s*name\s*[:\-]?\s*([A-Za-z ]+?)(?:\s*\n|\s*Address|\s*Account|\s*DOB|\s*Occupation|$)",
    ]
    name_parts = []
    for pat in patterns_name:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name_parts.append(m.group(1).strip())
    # If no specific name fields matched, try to extract the value after the last colon in any line containing 'name' (but not 'of account holder')
    if not name_parts:
        for line in text.splitlines():
            if 'name' in line.lower() and 'of account holder' not in line.lower():
                if ':' in line:
                    value = line.split(':')[-1].strip()
                    if value:
                        name_parts.append(value)
    # Remove duplicates while preserving order
    seen = set()
    name_parts_unique = []
    for part in name_parts:
        if part not in seen:
            name_parts_unique.append(part)
            seen.add(part)
    name = " ".join(name_parts_unique) if name_parts_unique else None
    
    # Try multiple account number patterns
    patterns = [
        r"client\s*csd\s*securities\s*account\s*no\s*[:\-]?\s*([0-9O]{5,})",  # Client CSD Securities Account No
        r"banking\s*information.*?account\s*number\s*[:\-]?\s*([0-9O]{5,})",  # Account Number under Banking information
        r"account\s*number\s*[:\-]?\s*([0-9O]{5,})",  # ACCOUNT NUMBER: 34007802837
        r"account\s*number\s*[:\-]?\s*([0-9O ]{5,})",  # ACCOUNT NUMBER with possible spaces
        r"account\s*no\s*[:\-]?\s*([0-9O]{5,})",     # ACCOUNT NO: 34007802837
        r"acct\s*no\s*[:\-]?\s*([0-9O]{5,})",        # ACCT NO: 34007802837
        r"a/c\s*no\s*[:\-]?\s*([0-9O]{5,})",         # A/C NO: 34007802837
        r"number\s*[:\-]?\s*([0-9O]{5,})",           # Just NUMBER: 34007802837
    ]
    
    account = None
    
    for pattern in patterns:
        m_account = re.search(pattern, text, re.IGNORECASE)
        if m_account:
            raw_acc = m_account.group(1).strip().replace(" ", "")
            account = raw_acc.replace("O", "0")  # Fix common OCR error
            break
    
    return name, account

def route_file(src_path):
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
        new_filename = filename  # keep original
        dest_dir = FAILED_DIR


    # Ensure unique filename at destination
    dest_path = os.path.join(dest_dir, new_filename)
    base, extn = os.path.splitext(new_filename)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_dir, f"{base}_{counter}{extn}")
        counter += 1

    if dest_dir == FAILED_DIR:
        # Just move the file as-is
        shutil.move(src_path, dest_path)
        print(f"[{dest_dir.upper()}] {filename} → {new_filename}")
        return dest_path

    if is_image:
        # Convert image to PDF and save as new file, then remove original
        if not os.path.exists(src_path):
            print(f"[SKIP] Source image missing before conversion: {src_path}")
            return None
        try:
            img = Image.open(src_path).convert("RGB")
            img.save(dest_path, "PDF", resolution=100.0)
            if os.path.exists(src_path):
                os.remove(src_path)
            print(f"[{dest_dir.upper()}] {filename} → {new_filename} (converted to PDF)")
            return dest_path
        except Exception as e:
            print(f"[ERROR] Failed to convert {filename} to PDF: {e}")
            # If conversion fails, move to failed as original (if it still exists)
            if os.path.exists(src_path):
                fail_path = os.path.join(FAILED_DIR, filename)
                shutil.move(src_path, fail_path)
                print(f"[FAILED] {filename} → {filename}")
                return fail_path
            else:
                print(f"[SKIP] Source image missing after failed conversion: {src_path}")
                return None
    else:
        shutil.move(src_path, dest_path)
        print(f"[{dest_dir.upper()}] {filename} → {new_filename}")
        return dest_path

# === Watcher ===



import threading

class ScanHandler(FileSystemEventHandler):
    _lock = threading.Lock()
    _timer = None

    def _delayed_batch_process(self):
        with self._lock:
            ScanHandler._timer = None
        time.sleep(5)  # Wait for all files to finish copying
        files = [f for f in os.listdir(SCAN_DIR) if f.lower().endswith((".pdf", ".png", ".jpg", ".jpeg"))]
        for fname in files:
            fpath = os.path.join(SCAN_DIR, fname)
            if not os.path.isfile(fpath):
                # File was already moved/processed, skip
                continue
            # Retry logic for each file
            last_exception = None
            for attempt in range(10):
                try:
                    if not os.path.isfile(fpath):
                        # File was moved during processing, skip further attempts
                        break
                    with open(fpath, 'rb') as f:
                        f.read(1)
                    route_file(fpath)
                    break
                except Exception as e:
                    last_exception = e
                    time.sleep(0.5)
            else:
                print(f"[ERROR] Failed to process {fpath} after multiple attempts: {last_exception}")

    def _schedule_batch(self):
        with self._lock:
            if ScanHandler._timer is not None:
                ScanHandler._timer.cancel()
            ScanHandler._timer = threading.Timer(0.5, self._delayed_batch_process)
            ScanHandler._timer.start()

    def on_created(self, event):
        if event.is_directory:
            return
        self._schedule_batch()

    def on_moved(self, event):
        if event.is_directory:
            return
        self._schedule_batch()

    def on_modified(self, event):
        # Optionally process modified files
        # if event.is_directory:
        #     return
        # self._schedule_batch()
        pass

def start_watcher():
    abs_scan_dir = os.path.abspath(SCAN_DIR)
    print(f"[WATCHING] {abs_scan_dir} -> (fully|partial|failed)")
    os.makedirs(SCAN_DIR, exist_ok=True)
    obs = Observer()
    obs.schedule(ScanHandler(), path=SCAN_DIR, recursive=False)
    obs.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()

if __name__ == "__main__":
    start_watcher()
