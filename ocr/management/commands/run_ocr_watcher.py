from django.core.management.base import BaseCommand
from ocr.watcher import start_watcher

class Command(BaseCommand):
    help = 'Starts the OCR folder watcher to process incoming scans'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Launching OCR watcher...'))
        try:
            start_watcher()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('OCR watcher stopped.'))
