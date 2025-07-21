from django.core.management.base import BaseCommand
import os
import sys

# Adjust the path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../ocr'))

from watcher import main  # Assuming your watcher.py has a main() function

class Command(BaseCommand):
    help = 'Runs the OCR watcher script'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting OCR watcher...'))
        main()
