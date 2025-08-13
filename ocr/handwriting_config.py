"""
Configuration settings for handwriting OCR optimization.
Adjust these settings based on your document types and handwriting quality.
"""

# OCR Configuration for Handwriting
HANDWRITING_OCR_CONFIG = {
    # Primary OCR configurations to try (in order of preference)
    'ocr_configs': [
        # LSTM neural network engine configurations (best for handwriting)
        '--oem 1 --psm 13',  # Raw line mode - excellent for handwriting
        '--oem 1 --psm 7',   # Single text line - good for clean handwriting
        '--oem 1 --psm 6',   # Single block - good for structured forms
        
        # Character-restricted configurations for names and numbers
        '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- ',
        '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ',
        '--psm 8 -c tessedit_char_whitelist=0123456789-',  # Numbers only for account fields
        
        # Fallback configurations
        '--psm 6',  # Single uniform block (default)
        '',         # Default tesseract settings
    ],
    
    # Image preprocessing settings
    'preprocessing': {
        'contrast_enhancement': 1.5,    # 1.0 = no change, >1.0 = more contrast
        'brightness_enhancement': 1.2,  # 1.0 = no change, >1.0 = brighter
        'enable_sharpening': True,      # Apply sharpening filter
        'enable_noise_reduction': True, # Apply median filter for noise
    },
    
    # Quality scoring weights
    'quality_scoring': {
        'length_weight': 1.0,       # Weight for text length
        'keyword_weight': 3.0,      # Weight for finding expected keywords
        'pattern_weight': 1.0,      # Weight for finding word/number patterns
        'noise_penalty': 2.0,       # Penalty for excessive special characters
    },
    
    # Handwriting-specific patterns (regex patterns that indicate good extraction)
    'handwriting_patterns': {
        'name_indicators': [
            r'surname.*individual',
            r'first\s*name',
            r'other\s*name',
            r'corporate\s*entities',
        ],
        'account_indicators': [
            r'account\s*no',
            r'csd\s*number',
            r'account\s*number',
            r'banking\s*information',
        ],
        'quality_patterns': [
            r'[A-Za-z]{3,}',    # Words with 3+ letters
            r'\d{3,}',          # Number sequences with 3+ digits
            r'[A-Z][a-z]+',     # Proper case words
        ]
    }
}

# Document type specific settings
DOCUMENT_TYPE_CONFIGS = {
    'bank_forms': {
        'expected_fields': ['surname', 'first_name', 'account_number'],
        'char_whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- ',
        'preferred_psm': 13,  # Raw line mode
    },
    
    'id_documents': {
        'expected_fields': ['name', 'id_number'],
        'char_whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
        'preferred_psm': 7,   # Single text line
    },
    
    'application_forms': {
        'expected_fields': ['surname', 'first_name', 'other_names', 'reference_number'],
        'char_whitelist': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-. ',
        'preferred_psm': 6,   # Single block
    }
}

# Advanced handwriting detection settings
HANDWRITING_DETECTION = {
    # Enable automatic handwriting vs print detection
    'auto_detect': True,
    
    # If handwriting is detected, apply these additional preprocessing steps
    'handwriting_preprocessing': {
        'gaussian_blur_radius': 0.5,    # Slight blur to connect broken characters
        'unsharp_mask': {
            'radius': 2,
            'percent': 150,
            'threshold': 3
        },
        'morphological_operations': True,  # Connect broken characters
    },
    
    # Confidence thresholds
    'confidence_thresholds': {
        'min_confidence': 30,      # Minimum OCR confidence to accept result
        'handwriting_threshold': 50,  # Below this = likely handwritten
        'print_threshold': 80,     # Above this = likely printed
    }
}

# Tips for improving handwriting recognition
HANDWRITING_TIPS = """
🖋️ HANDWRITING OCR OPTIMIZATION TIPS:

📝 For Document Writers:
• Use dark ink (black or blue) on white paper
• Write clearly with consistent letter spacing
• Avoid cursive writing for forms
• Use CAPITAL LETTERS for better recognition
• Ensure good lighting when scanning/photographing

📸 For Scanning/Photography:
• Use high resolution (300+ DPI for scans)
• Ensure good lighting with minimal shadows
• Keep the document flat and straight
• Avoid tilted or rotated documents
• Use contrast enhancement if the writing is faded

⚙️ For Technical Optimization:
• The system automatically tries multiple OCR configurations
• LSTM neural network engine (OEM 1) works best for handwriting
• PSM 13 (raw line mode) is optimal for handwritten text
• Character whitelisting improves accuracy for known field types
• Multiple preprocessing techniques are applied automatically

🎯 Expected Results:
• Clean handwriting: 85-95% accuracy
• Average handwriting: 70-85% accuracy  
• Poor handwriting: 50-70% accuracy
• Mixed print/handwriting: Variable, typically 80%+

The system will automatically select the best configuration for each document.
"""
