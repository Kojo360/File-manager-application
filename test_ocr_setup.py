#!/usr/bin/env python3
"""
Test OCR setup and configuration
Run this to verify OCR is working properly
"""
import sys
import os
import subprocess
from PIL import Image, ImageDraw

def test_tesseract():
    """Test tesseract installation and basic OCR"""
    print("=== Testing Tesseract ===")
    
    # Check if tesseract is in PATH
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        print(f"✅ Tesseract found: {result.stdout.split()[1] if result.stdout else 'Unknown'}")
        print(f"   Path: {subprocess.which('tesseract')}")
    except Exception as e:
        print(f"❌ Tesseract error: {e}")
        return False
    
    # Test pytesseract
    try:
        import pytesseract
        print(f"✅ pytesseract imported: {pytesseract.__version__}")
        print(f"   tesseract_cmd: {pytesseract.pytesseract.tesseract_cmd}")
        
        # Create a test image
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "ACCOUNT NO: 12345", fill='black')
        
        # Test OCR
        text = pytesseract.image_to_string(img).strip()
        print(f"✅ OCR test result: '{text}'")
        
        if "12345" in text:
            print("✅ OCR is working correctly!")
            return True
        else:
            print("⚠️  OCR working but text recognition may be inaccurate")
            return True
            
    except Exception as e:
        print(f"❌ pytesseract error: {e}")
        return False

def test_poppler():
    """Test poppler installation for PDF processing"""
    print("\n=== Testing Poppler ===")
    
    utilities = ['pdftoppm', 'pdfinfo', 'pdftotext']
    all_found = True
    
    for util in utilities:
        path = subprocess.which(util)
        if path:
            print(f"✅ {util}: {path}")
        else:
            print(f"❌ {util}: Not found")
            all_found = False
    
    # Test pdf2image
    try:
        from pdf2image import convert_from_path
        print("✅ pdf2image imported successfully")
        return True
    except Exception as e:
        print(f"❌ pdf2image error: {e}")
        return False

def test_django_ocr():
    """Test OCR through Django watcher"""
    print("\n=== Testing Django OCR Integration ===")
    
    try:
        # Import Django OCR modules
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ocr'))
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core', 'ocr'))
        
        from watcher import route_file, extract_text
        print("✅ Django OCR modules imported")
        
        # Create a test file
        test_dir = os.path.join(os.path.dirname(__file__), 'test_uploads')
        os.makedirs(test_dir, exist_ok=True)
        
        # Create test image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 50), "NAME: John Doe", fill='black')
        draw.text((20, 100), "ACCOUNT NO: 98765", fill='black')
        
        test_file = os.path.join(test_dir, 'test_account.png')
        img.save(test_file)
        
        # Test OCR extraction
        text = extract_text(test_file)
        print(f"✅ Extracted text: '{text.strip()}'")
        
        if "John Doe" in text and "98765" in text:
            print("✅ Django OCR integration working!")
            
        # Clean up
        os.remove(test_file)
        os.rmdir(test_dir)
        return True
        
    except Exception as e:
        print(f"❌ Django OCR error: {e}")
        return False

def main():
    """Run all OCR tests"""
    print("🔍 Testing OCR Setup\n")
    
    results = []
    results.append(test_tesseract())
    results.append(test_poppler())
    results.append(test_django_ocr())
    
    print(f"\n=== Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All OCR tests passed! Your setup is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
