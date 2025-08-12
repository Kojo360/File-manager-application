cd d:\File-manager-application
git add Dockerfile render.yaml
git commit -m "🚨 OPTION B: Switch to Docker - apt.txt failed on Render

Option A (apt.txt) failed - no apt package installation found in logs.
Switching to reliable Docker approach with guaranteed tesseract installation.

- Updated Dockerfile with tesseract-ocr and poppler-utils
- Changed render.yaml to env: docker
- Added build-time verification of package installation

This will ensure tesseract is definitely installed and available."
git push origin main
