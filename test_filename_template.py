import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_audio_downloader.advanced_filename_generation import FilenameTemplate

# Teste die FilenameTemplate-Klasse
template = FilenameTemplate('$artist - $title - $counter')
print('Template string:', template.template_string)
print('Placeholders:', template.placeholders)
print('Valid placeholders:', template.validate_placeholders())

metadata = {
    "artist": "Test Artist",
    "title": "Test Title"
}

result = template.render(metadata, 5)
print('Rendered result:', result)