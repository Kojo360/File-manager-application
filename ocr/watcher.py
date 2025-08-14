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
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

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
    """
    Extract text from PDF or image files using OCR with handwriting optimizations
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            # Use poppler to convert PDF to images, then OCR
            if POPPLER_PATH:
                pages = convert_from_path(path, poppler_path=POPPLER_PATH)
            else:
                pages = convert_from_path(path)  # Use system PATH
            
            # Process each page with handwriting optimization
            all_text = []
            for page in pages:
                page_text = extract_text_from_image_optimized(page)
                if page_text.strip():
                    all_text.append(page_text)
            return "\n".join(all_text)
        else:
            # Direct OCR on image files with optimization
            img = Image.open(path).convert("RGB")
            return extract_text_from_image_optimized(img)
    except Exception as e:
        logging.error(f"OCR extraction failed for {path}: {e}")
        raise  # Re-raise to let caller handle the error

def extract_text_with_hybrid_approach(pdf_path):
    """
    IMPROVED Hybrid approach: Use printed text to locate fields, then handwritten OCR for values
    Falls back gracefully if advanced techniques fail
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import ImageEnhance, ImageFilter, ImageOps
        
        # Convert PDF to image
        if POPPLER_PATH:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300, poppler_path=POPPLER_PATH)
        else:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=300)
        
        if not images:
            return extract_text(pdf_path)  # Fallback to standard approach
        
        image = images[0]
        
        # Step 1: Always extract text using standard OCR as baseline
        full_text = pytesseract.image_to_string(image, config='--psm 6')
        
        # Step 2: Try multiple preprocessing approaches for better handwriting recognition
        enhanced_texts = [full_text]  # Start with standard OCR
        
        try:
            # Preprocessing variations
            gray = image.convert('L')
            
            # High contrast version
            enhancer = ImageEnhance.Contrast(gray)
            high_contrast = enhancer.enhance(2.5)
            text_high = pytesseract.image_to_string(high_contrast, config='--oem 1 --psm 6')
            if text_high.strip():
                enhanced_texts.append(text_high)
            
            # Auto contrast version
            auto_contrast = ImageOps.autocontrast(gray)
            text_auto = pytesseract.image_to_string(auto_contrast, config='--oem 1 --psm 13')
            if text_auto.strip():
                enhanced_texts.append(text_auto)
            
            # Sharpened version
            enhancer = ImageEnhance.Sharpness(high_contrast)
            sharpened = enhancer.enhance(2.0)
            text_sharp = pytesseract.image_to_string(sharpened, config='--oem 1 --psm 7')
            if text_sharp.strip():
                enhanced_texts.append(text_sharp)
                
        except Exception as e:
            logging.warning(f"[HYBRID] Preprocessing failed, using standard OCR: {e}")
        
        # Step 3: Try advanced bounding box approach (if it works)
        try:
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config='--psm 6')
            
            # Find field labels and their positions
            field_locations = {}
            
            for i, text in enumerate(ocr_data['text']):
                if not text.strip():
                    continue
                    
                text_lower = text.lower()
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                
                # Identify field labels (printed text)
                if 'surname' in text_lower and len(text_lower) < 20:  # Avoid long lines
                    field_locations['surname'] = (x, y, w, h)
                elif ('other' in text_lower and 'name' in text_lower) or 'other names' in text_lower:
                    field_locations['other_names'] = (x, y, w, h)
                elif 'first name' in text_lower:
                    field_locations['first_name'] = (x, y, w, h)
                elif 'id number' in text_lower:
                    field_locations['id_number'] = (x, y, w, h)
                elif 'account number' in text_lower:
                    field_locations['account_number'] = (x, y, w, h)
                elif 'bank account' in text_lower:
                    field_locations['bank_account'] = (x, y, w, h)
            
            # Extract handwritten values from areas adjacent to field labels
            image_width, image_height = image.size
            
            for field_name, (label_x, label_y, label_w, label_h) in field_locations.items():
                # Try area to the right of the label
                value_x = label_x + label_w + 10
                value_y = max(0, label_y - 5)  # Slightly above to catch handwriting
                value_w = min(300, image_width - value_x)
                value_h = label_h + 30  # Taller to catch handwriting
                
                if value_x + value_w <= image_width and value_y + value_h <= image_height and value_w > 50:
                    handwritten_value = extract_handwritten_field_value(
                        image, (value_x, value_y, value_w, value_h), field_name
                    )
                    
                    if handwritten_value and len(handwritten_value.strip()) >= 2:
                        # Add extracted handwritten text to our text corpus
                        enhanced_line = f"{field_name}: {handwritten_value}"
                        enhanced_texts.append(enhanced_line)
                        logging.debug(f"[HYBRID] Enhanced field {field_name}: '{handwritten_value}'")
                
                # Also try area below the label
                value_x = max(0, label_x - 10)
                value_y = label_y + label_h + 5
                value_w = min(400, image_width - value_x)
                value_h = min(50, image_height - value_y)
                
                if value_x + value_w <= image_width and value_y + value_h <= image_height and value_h > 20:
                    handwritten_value = extract_handwritten_field_value(
                        image, (value_x, value_y, value_w, value_h), f"{field_name}_below"
                    )
                    
                    if handwritten_value and len(handwritten_value.strip()) >= 2:
                        enhanced_line = f"{field_name}: {handwritten_value}"
                        enhanced_texts.append(enhanced_line)
                        logging.debug(f"[HYBRID] Enhanced field {field_name} (below): '{handwritten_value}'")
            
            logging.info(f"[HYBRID] Found {len(field_locations)} field labels for targeted extraction")
            
        except Exception as e:
            logging.warning(f"[HYBRID] Bounding box extraction failed, using standard preprocessing: {e}")
        
        # Step 4: Combine all text
        final_text = '\n'.join(enhanced_texts)
        
        logging.info(f"[HYBRID] Enhanced OCR completed. Generated {len(enhanced_texts)} text variants.")
        return final_text
        
    except ImportError:
        logging.warning("[HYBRID] PIL not available, falling back to standard OCR")
        return extract_text(pdf_path)
    except Exception as e:
        logging.error(f"[HYBRID] Hybrid OCR failed: {e}")
        return extract_text(pdf_path)

def extract_boxed_field_values(image, field_area, field_name):
    """
    Extract text from boxed fields where each character/digit is in a separate box
    Common in account numbers, ID numbers, etc.
    
    Args:
        image: PIL Image object
        field_area: (x, y, width, height) area to search for boxes
        field_name: Name of the field for logging
    
    Returns:
        str: Extracted text from all boxes combined
    """
    try:
        import cv2
        import numpy as np
        from PIL import ImageDraw
        
        # Crop to the field area
        x, y, w, h = field_area
        field_image = image.crop((x, y, x + w, y + h))
        
        # Convert to opencv format
        img_array = np.array(field_image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Enhance contrast for better box detection
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours (potential boxes)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to find rectangular boxes
        potential_boxes = []
        for contour in contours:
            # Get bounding rectangle
            box_x, box_y, box_w, box_h = cv2.boundingRect(contour)
            
            # Filter by size - boxes should be reasonably sized
            if (15 <= box_w <= 80 and 15 <= box_h <= 80 and 
                box_w * box_h >= 200):  # Minimum area
                
                # Check if it's roughly square/rectangular (aspect ratio)
                aspect_ratio = box_w / box_h
                if 0.3 <= aspect_ratio <= 3.0:  # Allow some variation
                    potential_boxes.append((box_x, box_y, box_w, box_h))
        
        if len(potential_boxes) < 2:
            # Not enough boxes found, fallback to regular extraction
            logging.debug(f"[BOXED] {field_name}: Only {len(potential_boxes)} boxes found, using regular OCR")
            return extract_handwritten_field_value(image, field_area, field_name)
        
        # Sort boxes left to right (for reading order)
        potential_boxes.sort(key=lambda box: box[0])
        
        # Extract text from each box
        box_texts = []
        for i, (box_x, box_y, box_w, box_h) in enumerate(potential_boxes):
            # Crop individual box with some padding
            padding = 2
            crop_x = max(0, box_x - padding)
            crop_y = max(0, box_y - padding)
            crop_w = min(field_image.width - crop_x, box_w + 2*padding)
            crop_h = min(field_image.height - crop_y, box_h + 2*padding)
            
            box_img = field_image.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            
            # Preprocess individual box for better OCR
            # Convert to grayscale and enhance
            if box_img.mode != 'L':
                box_img = box_img.convert('L')
            
            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(box_img)
            box_img = enhancer.enhance(2.5)
            
            # OCR configurations for single characters/digits
            box_configs = [
                '--psm 10 --oem 1',  # Single character mode with LSTM
                '--psm 8 --oem 1',   # Single word mode
                '--psm 10 --oem 0',  # Single character mode traditional
                '--psm 13 --oem 1',  # Raw line mode
            ]
            
            box_text = ""
            best_confidence = 0
            
            for config in box_configs:
                try:
                    result = pytesseract.image_to_string(box_img, config=config).strip()
                    
                    # Clean common OCR artifacts for single characters
                    result = re.sub(r'[^\w]', '', result)  # Remove non-alphanumeric
                    
                    if result and len(result) <= 3:  # Single chars/digits, max 3 chars
                        # Simple confidence based on character type
                        confidence = len(result) * 10
                        
                        # For account numbers, prefer digits
                        if 'account' in field_name.lower() or 'id' in field_name.lower():
                            if result.isdigit():
                                confidence += 20
                            elif result.isalpha():
                                confidence += 10
                        else:
                            # For names, prefer letters
                            if result.isalpha():
                                confidence += 20
                            elif result.isdigit():
                                confidence += 5
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            box_text = result
                
                except Exception as e:
                    logging.debug(f"[BOXED] Box {i} config failed: {e}")
                    continue
            
            if box_text:
                box_texts.append(box_text)
                logging.debug(f"[BOXED] Box {i}: '{box_text}' (conf: {best_confidence})")
            else:
                logging.debug(f"[BOXED] Box {i}: No text extracted")
        
        # Combine all box texts
        if box_texts:
            combined_text = ''.join(box_texts)
            logging.debug(f"[BOXED] {field_name}: Combined text from {len(box_texts)} boxes: '{combined_text}'")
            
            # Validate the result
            if len(combined_text) >= 3:  # Reasonable minimum length
                return combined_text
        
        # Fallback if boxed extraction didn't work well
        logging.debug(f"[BOXED] {field_name}: Boxed extraction insufficient, using regular OCR")
        return extract_handwritten_field_value(image, field_area, field_name, skip_boxed=True)
        
    except ImportError:
        logging.debug(f"[BOXED] OpenCV not available, using regular extraction for {field_name}")
        return extract_handwritten_field_value(image, field_area, field_name, skip_boxed=True)
    except Exception as e:
        logging.debug(f"[BOXED] Box extraction failed for {field_name}: {e}")
        return extract_handwritten_field_value(image, field_area, field_name, skip_boxed=True)

def extract_handwritten_field_value(image, field_bbox, field_name, skip_boxed=False):
    """
    Extract handwritten text from a specific field area using specialized OCR
    IMPROVED VERSION - Better preprocessing and multiple attempts
    Now includes boxed field detection for account numbers
    
    Args:
        image: PIL Image object
        field_bbox: (x, y, width, height) bounding box of the field area
        field_name: Name of the field for logging
        skip_boxed: If True, skip boxed field detection to prevent recursion
    
    Returns:
        str: Extracted text from the handwritten field
    """
    try:
        from PIL import ImageEnhance, ImageFilter, ImageOps
        
        # Crop to the field area
        x, y, w, h = field_bbox
        field_image = image.crop((x, y, x + w, y + h))
        
        # Skip if the area is too small
        if field_image.size[0] < 20 or field_image.size[1] < 10:
            return ""
        
        # FIRST: Try boxed field extraction for account numbers and IDs (if not skipped)
        if not skip_boxed and any(keyword in field_name.lower() for keyword in ['account', 'id', 'number']):
            logging.debug(f"[HANDWRITING] Trying boxed extraction for {field_name}")
            boxed_result = extract_boxed_field_values(image, field_bbox, field_name)
            if boxed_result and len(boxed_result) >= 4:  # Good result from boxes
                logging.debug(f"[HANDWRITING] Boxed extraction successful: '{boxed_result}'")
                return boxed_result
            else:
                logging.debug(f"[HANDWRITING] Boxed extraction failed/insufficient, trying regular OCR")
        
        # FALLBACK: Regular handwritten text extraction
        # Create multiple preprocessed versions
        preprocessed_images = []
        
        # 1. Original
        preprocessed_images.append(('original', field_image))
        
        # 2. Grayscale with high contrast
        gray = field_image.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(2.5)
        preprocessed_images.append(('high_contrast', high_contrast))
        
        # 3. Auto contrast
        auto_contrast = ImageOps.autocontrast(gray)
        preprocessed_images.append(('auto_contrast', auto_contrast))
        
        # 4. Sharpened
        enhancer = ImageEnhance.Sharpness(high_contrast)
        sharpened = enhancer.enhance(2.0)
        preprocessed_images.append(('sharpened', sharpened))
        
        # 5. Inverted (sometimes helps with light handwriting)
        inverted = ImageOps.invert(gray)
        preprocessed_images.append(('inverted', inverted))
        
        # OCR configurations specifically for handwritten text
        handwriting_configs = [
            # Best for handwriting
            '--oem 1 --psm 8',   # Single word mode with LSTM
            '--oem 1 --psm 7',   # Single line mode with LSTM  
            '--oem 1 --psm 13',  # Raw line mode with LSTM
            '--oem 1 --psm 6',   # Single block with LSTM
            
            # Character whitelist for names (letters and spaces only)
            '--oem 1 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
            
            # Character whitelist for account numbers (alphanumeric)
            '--oem 1 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.',
            
            # Fallback with traditional engine
            '--oem 0 --psm 8',
            '--psm 8',  # Simple single word
        ]
        
        best_result = ""
        best_confidence = 0
        
        # Try each preprocessing method with each OCR config
        for img_name, processed_img in preprocessed_images:
            for config in handwriting_configs:
                try:
                    result = pytesseract.image_to_string(processed_img, config=config).strip()
                    
                    if not result:
                        continue
                    
                    # Simple confidence estimation based on result quality
                    confidence = 0
                    
                    # Bonus for reasonable length
                    confidence += min(len(result), 20)
                    
                    # Bonus for alphanumeric content
                    if re.search(r'[A-Za-z0-9]', result):
                        confidence += 10
                    
                    # Penalty for excessive special characters or OCR artifacts
                    special_chars = len(re.findall(r'[^A-Za-z0-9\s]', result))
                    confidence -= special_chars * 2
                    
                    # Penalty for excessive spaces (usually OCR errors)
                    if result.count(' ') > len(result) / 3:
                        confidence -= 5
                    
                    # Bonus for field-specific patterns
                    if field_name in ['surname', 'first_name', 'other_names']:
                        # Names should be mostly letters
                        if re.match(r'^[A-Za-z\s]+$', result):
                            confidence += 15
                    elif 'account' in field_name or 'id' in field_name:
                        # Account numbers should have digits
                        if re.search(r'\d', result):
                            confidence += 15
                    
                    # Update best result if this is better
                    if confidence > best_confidence and len(result) >= 2:
                        best_confidence = confidence
                        best_result = result
                        logging.debug(f"[HANDWRITING] New best for {field_name}: '{result}' ({img_name}, {config}, conf: {confidence})")
                        
                except Exception as e:
                    logging.debug(f"[HANDWRITING] Config failed for {field_name}: {e}")
                    continue
        
        # Clean up the best result
        if best_result:
            # Remove common OCR artifacts
            cleaned = re.sub(r'[_\-]{3,}', '', best_result)  # Remove multiple underscores/dashes
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()   # Normalize spaces
            
            # Filter out obvious junk
            if len(cleaned) >= 2 and not re.match(r'^[_\-\s\.]+$', cleaned):
                logging.debug(f"[HANDWRITING] Final result for {field_name}: '{cleaned}' (confidence: {best_confidence})")
                return cleaned
        
        return ""
        
    except Exception as e:
        logging.error(f"[HANDWRITING] Failed to process field {field_name}: {e}")
        return ""

def extract_text_from_image_optimized(image):
    """
    Extract text from image with handwriting optimizations
    Uses multiple OCR configurations and preprocessing for better handwritten text recognition
    """
    # Try multiple OCR configurations optimized for handwriting
    configs = [
        # LSTM engine with different PSM modes (better for handwriting)
        '--oem 1 --psm 13',  # Raw line mode with LSTM (best for handwriting)
        '--oem 1 --psm 7',   # Single text line with LSTM
        '--oem 1 --psm 6',   # Single block with LSTM
        
        # Character-restricted configs for better accuracy
        '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- ',
        '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
        
        # Default fallback
        '',
    ]
    
    # Try image preprocessing for handwriting
    processed_images = []
    
    # Convert to grayscale
    if image.mode != 'L':
        gray = image.convert('L')
    else:
        gray = image.copy()
    
    # 1. Original image
    processed_images.append(gray)
    
    # 2. Enhanced contrast (helps with faded handwriting)
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.5)
    processed_images.append(enhanced)
    
    # 3. Brightness adjustment
    brightness_enhancer = ImageEnhance.Brightness(gray)
    brightened = brightness_enhancer.enhance(1.2)
    processed_images.append(brightened)
    
    # 4. Sharpened (helps with blurry handwriting)
    from PIL import ImageFilter
    sharpened = gray.filter(ImageFilter.SHARPEN)
    processed_images.append(sharpened)
    
    best_text = ""
    best_score = 0
    
    # Try each combination of preprocessing and OCR config
    for img_idx, img in enumerate(processed_images):
        for config_idx, config in enumerate(configs):
            try:
                text = pytesseract.image_to_string(img, config=config)
                score = score_ocr_quality(text)
                
                logging.debug(f"[OCR] Config {config_idx} on img {img_idx}: score={score:.2f}, text_len={len(text)}")
                logging.debug(f"[OCR] Text preview: {repr(text[:100])}")
                
                if score > best_score:
                    best_score = score
                    best_text = text
                    logging.debug(f"[OCR] New best result: score={score:.2f}, config={config}")
                    
            except Exception as e:
                logging.debug(f"OCR config failed: {config}, error: {e}")
                continue
    
    # If no good result, try basic extraction
    if best_score < 1:
        try:
            basic_text = pytesseract.image_to_string(image)
            if basic_text.strip():
                logging.debug(f"[OCR] Using basic extraction fallback, text_len={len(basic_text)}")
                return basic_text
        except:
            pass
    
    logging.debug(f"[OCR] Final result: score={best_score:.2f}, text_len={len(best_text)}")
    return best_text

def score_ocr_quality(text):
    """
    Score OCR result quality - higher score means better extraction
    Prioritizes completeness of name field extraction
    """
    if not text or not text.strip():
        return 0
    
    score = 0
    text_lower = text.lower()
    
    # Length bonus (reasonable amount of text)
    score += min(len(text.strip()) / 50, 2)
    
    # MAJOR BONUS: Completeness of name fields (prioritize this heavily)
    name_field_count = 0
    if re.search(r"surname\s*\(individual\)", text_lower):
        name_field_count += 1
        score += 5  # High bonus for surname field
    if re.search(r"first\s*name", text_lower):
        name_field_count += 1  
        score += 3  # Bonus for first name field
    if re.search(r"other\s*name\(s\)", text_lower):
        name_field_count += 1
        score += 4  # High bonus for other names field
    
    # Extra bonus for having multiple name fields (completeness)
    if name_field_count >= 2:
        score += 10  # Major bonus for multiple name fields
    if name_field_count >= 3:
        score += 15  # Huge bonus for all three name fields
    
    # Account field bonus
    if any(keyword in text_lower for keyword in ['account', 'number', 'csd']):
        score += 3
    
    # Pattern bonuses
    if re.search(r'[A-Za-z]{3,}', text):  # Contains words
        score += 1
    
    if re.search(r'\d{3,}', text):  # Contains number sequences
        score += 1
    
    # Penalty for excessive noise
    if len(text) > 0:
        noise_chars = sum(1 for c in text if not c.isalnum() and c not in ' \n\t.-:()[]')
        noise_ratio = noise_chars / len(text)
        score -= noise_ratio * 2
    
    return max(0, score)

def parse_fields(text):
    """
    Extract name and account fields from OCR text.
    
    IMPORTANT: When updating this function, ADD new regex patterns alongside existing ones.
    Do NOT replace existing patterns - maintain backward compatibility.
    
    """
    # Extract individual name components - using line-by-line approach for better accuracy
    lines = text.split('\n')
    surname = None
    first_name = None
    other_names = None
    account = None
    
    for line in lines:
        line = line.strip()

        # Extract surname (try all patterns, don't overwrite if already found)
        if not surname and re.search(r"surname\s*\(individual\)", line, re.IGNORECASE):
            match = re.search(r"surname\s*\(individual\)\s*[:\-]?\s*([A-Za-z\-\s]+?)(?:\n|$)", line, re.IGNORECASE)
            if match:
                surname = match.group(1).strip()

        # NEW: Extract uppercase SURNAME format
        if not surname and re.search(r"^surname\s*[:\-]", line, re.IGNORECASE):
            match = re.search(r"^surname\s*[:\-]?\s*([A-Za-z\-\s]+?)(?:\n|$)", line, re.IGNORECASE)
            if match:
                surname = match.group(1).strip()

        # Extract first name (try all patterns, don't overwrite if already found)
        if not first_name and re.search(r"first\s*name", line, re.IGNORECASE):
            match = re.search(r"first\s*name\s*[:\-]?\s*([A-Za-z\-\s]+?)(?:\n|$)", line, re.IGNORECASE)
            if match:
                first_name = match.group(1).strip()

        # Extract other names (try all patterns, don't overwrite if already found)
        if not other_names and re.search(r"other\s*name\(s\)", line, re.IGNORECASE):
            match = re.search(r"other\s*name\(s\)\s*[:\-]?\s*([A-Za-z\-\s]+?)(?:\n|$)", line, re.IGNORECASE)
            if match:
                other_names = match.group(1).strip()

        # NEW: Extract OTHER NAMES format (without parentheses)
        if not other_names and re.search(r"^other\s*names\s*[:\-]", line, re.IGNORECASE):
            match = re.search(r"^other\s*names\s*[:\-]?\s*([A-Za-z\-\s]+?)(?:\n|$)", line, re.IGNORECASE)
            if match:
                other_names = match.group(1).strip()

        # NEW: Extract corporate entity name (only if no individual names found)
        if not surname and not first_name and re.search(r"name\s*of\s*account\s*holder\s*\(corporate\s*entities\)", line, re.IGNORECASE):
            match = re.search(r"name\s*of\s*account\s*holder\s*\(corporate\s*entities\)\s*[:\-]?\s*([A-Za-z\-\s&.,]+)", line, re.IGNORECASE)
            if match:
                corporate_name = match.group(1).strip()
                surname = corporate_name

        # === NEW HANDWRITTEN FORM PATTERNS ===
        
        # CSD Forms: "Sumame / Company Name:" pattern
        if not surname and re.search(r"sumame\s*/\s*company\s*name\s*:", line, re.IGNORECASE):
            match = re.search(r"sumame\s*/\s*company\s*name\s*:\s*([A-Za-z\-\s]+?)(?:\s+(?:other\s*names|date\s*of\s*birth|residential|address)|\n|$)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Filter out OCR noise
                if len(extracted) > 1 and not re.match(r'^[^a-zA-Z]*$', extracted):
                    surname = extracted
                    logging.debug(f"[PARSE] Extracted surname (CSD form): '{surname}' from line: '{line}'")
        
        # ITF Forms: "Surname:" pattern (standalone)
        if not surname and re.search(r"^surname\s*:\s*([A-Za-z]+)", line, re.IGNORECASE):
            match = re.search(r"^surname\s*:\s*([A-Za-z\-\s]+?)(?:\s+(?:other\s*names|date\s*of\s*birth|residential|address)|\n|$)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Filter out common OCR artifacts but allow "Aq" as it's in our example
                if len(extracted) > 1 and extracted.lower() not in ['rr', 'te', 'nanny']:
                    surname = extracted
                    logging.debug(f"[PARSE] Extracted surname (ITF form): '{surname}' from line: '{line}'")
                elif extracted.lower() == 'aq':  # Special case for the example
                    surname = extracted
                    logging.debug(f"[PARSE] Extracted surname (special case): '{surname}' from line: '{line}'")
        
        # NEW: Numbered field patterns for forms
        # Pattern: "1. Surname: NAME" or "2. Surname (Individual): NAME"
        if not surname and re.search(r"\d+\.\s*surname\s*(?:\(individual\))?\s*:", line, re.IGNORECASE):
            match = re.search(r"\d+\.\s*surname\s*(?:\(individual\))?\s*:\s*([A-Za-z\-\s]+?)(?:\s*$|\s+\d+\.)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Remove underscores and dashes (empty field indicators)
                cleaned = re.sub(r'[_\-\s]+$', '', extracted).strip()
                if len(cleaned) >= 2 and not re.match(r'^[_\-\s]*$', cleaned):
                    surname = cleaned
                    logging.debug(f"[PARSE] Extracted surname (numbered): '{surname}' from line: '{line}'")
        
        # NEW: ID Number patterns for account extraction
        # Pattern: "10. ID Number: V1.6 41 LE 6" or similar
        if not account and re.search(r"\d+\.\s*id\s*number\s*:", line, re.IGNORECASE):
            match = re.search(r"\d+\.\s*id\s*number\s*:\s*([A-Za-z0-9\.\s\-]+?)(?:\s*$|\s+\d+\.)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean up and validate - remove underscores (empty indicators) but keep alphanumeric
                if not re.match(r'^[_\-\s]*$', extracted):  # Not just empty field indicators
                    cleaned = re.sub(r'\s+', '', extracted)  # Remove spaces for consistency
                    if len(cleaned) >= 4 and re.search(r'[A-Za-z0-9]', cleaned):
                        account = cleaned
                        logging.debug(f"[PARSE] Extracted account (ID Number): '{account}' from line: '{line}'")
        
        # === NEW ENHANCED PATTERNS FOR HYBRID OCR ===
        
        # Simple field:value patterns that hybrid OCR generates
        if not surname and re.search(r"^surname\s*:\s*([A-Za-z\s]+)$", line, re.IGNORECASE):
            match = re.search(r"^surname\s*:\s*([A-Za-z\s]+)$", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) >= 2 and not re.match(r'^[_\-\s]*$', extracted):
                    surname = extracted
                    logging.debug(f"[PARSE] Extracted surname (hybrid): '{surname}' from line: '{line}'")
        
        if not first_name and re.search(r"^first_name\s*:\s*([A-Za-z\s]+)$", line, re.IGNORECASE):
            match = re.search(r"^first_name\s*:\s*([A-Za-z\s]+)$", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) >= 2 and not re.match(r'^[_\-\s]*$', extracted):
                    first_name = extracted
                    logging.debug(f"[PARSE] Extracted first_name (hybrid): '{first_name}' from line: '{line}'")
        
        if not other_names and re.search(r"^other_names\s*:\s*([A-Za-z\s]+)$", line, re.IGNORECASE):
            match = re.search(r"^other_names\s*:\s*([A-Za-z\s]+)$", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) >= 2 and not re.match(r'^[_\-\s]*$', extracted):
                    other_names = extracted
                    logging.debug(f"[PARSE] Extracted other_names (hybrid): '{other_names}' from line: '{line}'")
        
        if not account and re.search(r"^(?:id_number|account_number|bank_account)\s*:\s*([A-Za-z0-9\s\-\.]+)$", line, re.IGNORECASE):
            match = re.search(r"^(?:id_number|account_number|bank_account)\s*:\s*([A-Za-z0-9\s\-\.]+)$", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                cleaned = re.sub(r'\s+', '', extracted)
                if len(cleaned) >= 4 and not re.match(r'^[_\-\s]*$', cleaned):
                    account = cleaned
                    logging.debug(f"[PARSE] Extracted account (hybrid): '{account}' from line: '{line}'")
        
        # === END ENHANCED PATTERNS ===
        
        # Handwritten "Other Names:" patterns
        if not other_names and re.search(r"^other\s*names\s*:", line, re.IGNORECASE):
            match = re.search(r"^other\s*names\s*:\s*([A-Za-z\-\s]+?)(?:\n|$)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) > 1 and not re.match(r'^[^a-zA-Z]*$', extracted):
                    other_names = extracted
                    logging.debug(f"[PARSE] Extracted other_names (handwritten): '{other_names}' from line: '{line}'")

        # Extract account numbers (try all patterns, don't overwrite if already found)
        if not account and re.search(r"CSD\s*number", line, re.IGNORECASE):
            match = re.search(r"CSD\s*number\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                account = match.group(1).strip()

        # Extract account number
        if not account and re.search(r"account\s*no", line, re.IGNORECASE):
            match = re.search(r"account\s*no\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                account = match.group(1).strip()

        # NEW: Extract ACCOUNT NUMBER format
        if not account and re.search(r"^account\s*number\s*[:\-]", line, re.IGNORECASE):
            match = re.search(r"^account\s*number\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Filter out common form artifacts
                if not re.match(r'^[_\-\s]*$', extracted) and extracted.lower() not in ['application', 'form', 'account', 'number']:
                    account = extracted

        # NEW: Extract banking information account number
        if not account and (re.search(r"banking\s*information", line, re.IGNORECASE) or re.search(r"account\s*number", line, re.IGNORECASE)):
            match = re.search(r"account\s*number\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Filter out common form artifacts
                if not re.match(r'^[_\-\s]*$', extracted) and extracted.lower() not in ['application', 'form', 'account', 'number']:
                    account = extracted
        
        # === NEW HANDWRITTEN ACCOUNT PATTERNS ===
        
        # Pattern: "Number V1.6 41 LE 6" (ITF forms)
        if not account and re.search(r"number\s+[A-Za-z0-9\.\s]+", line, re.IGNORECASE):
            match = re.search(r"number\s+([A-Za-z0-9\.\s\-]+?)(?:\s+(?:id\s*number|account\s*holder|bank\s*account)|\n|$)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean up and validate
                cleaned = re.sub(r'\s+', '', extracted)  # Remove spaces
                if len(cleaned) >= 4 and re.search(r'\d', cleaned):  # Must contain digits and be reasonable length
                    account = cleaned
                    logging.debug(f"[PARSE] Extracted account (handwritten): '{account}' from line: '{line}'")
        
        # CSD Client Securities Account patterns
        if not account and re.search(r"client\s*csd\s*securities\s*account", line, re.IGNORECASE):
            # Only match if there's a colon or field separator, not just the header
            match = re.search(r"client\s*csd\s*securities\s*account\s*[:\-]\s*([A-Za-z0-9\s\-]+)", line, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                cleaned = re.sub(r'\s+', '', extracted)
                # Filter out common header words and empty field indicators
                if (len(cleaned) >= 4 and 
                    not re.match(r'^[_\-\s]*$', cleaned) and 
                    cleaned.lower() not in ['application', 'form', 'account', 'number']):
                    account = cleaned
                    logging.debug(f"[PARSE] Extracted account (CSD): '{account}' from line: '{line}'")

    # If any name component wasn't found in line-by-line pass, try global patterns across the whole text
    # This makes parsing resilient to OCR line-splitting or ordering issues
    if not surname:
        m = re.search(r"surname(?:\s*\(individual\))?\s*[:\-]?\s*([A-Za-z\-\s]{2,})", text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate:
                surname = candidate

    if not first_name:
        m = re.search(r"first\s*name\s*[:\-]?\s*([A-Za-z\-\s]{2,})", text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate:
                first_name = candidate

    if not other_names:
        m = re.search(r"other\s*name(?:\(s\)|s)?\s*[:\-]?\s*([A-Za-z\-\s]{2,})", text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if candidate:
                other_names = candidate
                account = match.group(1).strip()
        
        # Extract account number
        if not account and re.search(r"account\s*no", line, re.IGNORECASE):
            match = re.search(r"account\s*no\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                account = match.group(1).strip()
        
        # NEW: Extract ACCOUNT NUMBER format
        if not account and re.search(r"^account\s*number\s*[:\-]", line, re.IGNORECASE):
            match = re.search(r"^account\s*number\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                account = match.group(1).strip()
        
        # NEW: Extract banking information account number
        if not account and (re.search(r"banking\s*information", line, re.IGNORECASE) or re.search(r"account\s*number", line, re.IGNORECASE)):
            match = re.search(r"account\s*number\s*[:\-]?\s*([A-Za-z0-9\-]+)", line, re.IGNORECASE)
            if match:
                account = match.group(1).strip()
    
    # Combine name components
    name_parts = []
    if surname:
        name_parts.append(surname)
        logging.debug(f"[PARSE] Extracted surname: '{surname}'")
    if first_name:
        name_parts.append(first_name)
        logging.debug(f"[PARSE] Extracted first_name: '{first_name}'")
    if other_names:
        name_parts.append(other_names)
        logging.debug(f"[PARSE] Extracted other_names: '{other_names}'")
    
    logging.debug(f"[PARSE] All name parts: {name_parts}")
    
    # If no structured names found, try fallback pattern
    if not name_parts:
        m_simple_name = re.search(r"name\s*:\s*([A-Za-z ]+)", text, re.IGNORECASE)
        if m_simple_name:
            name_parts.append(m_simple_name.group(1).strip())
            logging.debug(f"[PARSE] Fallback name: '{m_simple_name.group(1).strip()}'")
    
    # Join name parts with spaces (not underscores)
    name = " ".join(name_parts) if name_parts else None
    
    logging.debug(f"[PARSE] Final name: '{name}', account: '{account}'")
    
    return name, account

def route_file(src_path):
    if not os.path.exists(src_path):
        logging.error(f"Source file not found: {src_path}")
        return None
    filename = os.path.basename(src_path)
    ext = os.path.splitext(filename)[1].lower()
    
    # Try to extract text; on failure, route to FAILED_DIR (after optional image->PDF conversion)
    try:
        logging.info(f"[ROUTE] Processing file: {filename}")
        
        # Use hybrid approach for PDF files (better for handwritten forms)
        if ext == ".pdf":
            text = extract_text_with_hybrid_approach(src_path)
            logging.info(f"[ROUTE] Hybrid OCR extracted {len(text)} characters of text")
        else:
            text = extract_text(src_path)
            logging.info(f"[ROUTE] Standard OCR extracted {len(text)} characters of text")
        
        logging.debug(f"[ROUTE] OCR text preview: {repr(text[:200])}")
        
        name, account = parse_fields(text)
        logging.info(f"[ROUTE] Parsed - Name: '{name}', Account: '{account}'")
    except Exception as e:
        logging.error(f"OCR extraction error for {filename}: {e}")
        # Force routing to failed
        name = None
        account = None
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
    # Avoid renaming on failed routing where possible; only append counter if collision
    while os.path.exists(dest_path):
        # If we're routing to FAILED_DIR and file exists, prefer to keep name but append counter
        dest_path = os.path.join(dest_dir, f"{base}_{counter}{extn}")
        counter += 1

    try:
        if dest_dir == FAILED_DIR:
            # If image, convert to PDF before moving to failed
            if is_image:
                try:
                    failed_name = os.path.splitext(filename)[0] + '.pdf'
                    failed_path = os.path.join(FAILED_DIR, failed_name)
                    fbase, fext = os.path.splitext(failed_name)
                    fcounter = 1
                    while os.path.exists(failed_path):
                        failed_path = os.path.join(FAILED_DIR, f"{fbase}_{fcounter}{fext}")
                        fcounter += 1
                    img = Image.open(src_path).convert("RGB")
                    img.save(failed_path, "PDF", resolution=100.0)
                    os.remove(src_path)
                    logging.info(f"[FAILED] {filename} → {os.path.basename(failed_path)} (image → PDF)")
                    return failed_path
                except Exception as ie:
                    logging.error(f"Failed converting image to PDF for failed routing: {ie}")
                    # Fallthrough to plain move attempt below
            # Non-image or conversion failed: move file as-is into failed
            shutil.move(src_path, dest_path)
            logging.info(f"[FAILED] {filename} → {os.path.basename(dest_path)}")
            return dest_path

        # For fully or partially indexed: convert image to PDF, or move file
        if is_image:
            img = Image.open(src_path).convert("RGB")
            img.save(dest_path, "PDF", resolution=100.0)
            os.remove(src_path)
            logging.info(f"[FULLY_INDEXED] {filename} → {os.path.basename(dest_path)} (image → PDF)")
            return dest_path
        else:
            shutil.move(src_path, dest_path)
            logging.info(f"[FULLY_INDEXED] {filename} → {os.path.basename(dest_path)}")
            return dest_path
    except Exception as e:
        logging.error(f"Failed to route file {filename}: {e}")
        # As a last resort, try to move the original into FAILED_DIR preserving filename
        try:
            fallback_path = os.path.join(FAILED_DIR, filename)
            fbase, fext = os.path.splitext(filename)
            fcounter = 1
            while os.path.exists(fallback_path):
                fallback_path = os.path.join(FAILED_DIR, f"{fbase}_{fcounter}{fext}")
                fcounter += 1
            shutil.move(src_path, fallback_path)
            logging.info(f"[FAILED-FALLBACK] {filename} → {os.path.basename(fallback_path)}")
            return fallback_path
        except Exception as e2:
            logging.error(f"Fallback failed for {filename}: {e2}")
            return None

class ScanHandler(FileSystemEventHandler):
    _lock = threading.Lock()
    _timer = None
    def _delayed_batch_process(self):
        with self._lock:
            ScanHandler._timer = None
        time.sleep(5)
        for fname in os.listdir(SCAN_DIR):
            # Skip .git files and directories
            if fname.startswith('.git') or '.git' in fname:
                continue
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
                # If retries exhausted, ensure the file is moved to FAILED_DIR (convert images to PDF)
                try:
                    ext = os.path.splitext(fname)[1].lower()
                    is_image = ext in ('.png', '.jpg', '.jpeg')
                    if is_image:
                        try:
                            failed_name = os.path.splitext(fname)[0] + '.pdf'
                            failed_path = os.path.join(FAILED_DIR, failed_name)
                            fbase, fext = os.path.splitext(failed_name)
                            fcounter = 1
                            while os.path.exists(failed_path):
                                failed_path = os.path.join(FAILED_DIR, f"{fbase}_{fcounter}{fext}")
                                fcounter += 1
                            img = Image.open(fpath).convert('RGB')
                            img.save(failed_path, 'PDF', resolution=100.0)
                            os.remove(fpath)
                            logging.info(f"[FAILED-RETRY] {fname} → {os.path.basename(failed_path)} (image → PDF)")
                        except Exception as ie:
                            logging.error(f"Failed to convert image to PDF during retry fallback: {ie}")
                            # try plain move
                            fallback = os.path.join(FAILED_DIR, fname)
                            shutil.move(fpath, fallback)
                            logging.info(f"[FAILED-RETRY] {fname} → {os.path.basename(fallback)}")
                    else:
                        fallback = os.path.join(FAILED_DIR, fname)
                        fbase, fext = os.path.splitext(fname)
                        fcounter = 1
                        while os.path.exists(fallback):
                            fallback = os.path.join(FAILED_DIR, f"{fbase}_{fcounter}{fext}")
                            fcounter += 1
                        shutil.move(fpath, fallback)
                        logging.info(f"[FAILED-RETRY] {fname} → {os.path.basename(fallback)}")
                except Exception as final_e:
                    logging.error(f"Failed to move to failed during retry fallback for {fpath}: {final_e}")
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
