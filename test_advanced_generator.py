import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_audio_downloader.advanced_filename_generation import AdvancedFilenameGenerator

# Erstelle ein temporäres Verzeichnis
temp_dir = tempfile.mkdtemp()
print('Temp directory:', temp_dir)

try:
    # Teste den AdvancedFilenameGenerator
    gen = AdvancedFilenameGenerator(temp_dir)
    print('Default templates:', list(gen.templates.keys()))
    print('Current template:', gen.current_template)
    
    # Füge eine benutzerdefinierte Vorlage hinzu
    success = gen.add_template('test', '$artist - $title - $counter')
    print('Add template success:', success)
    print('Templates after add:', list(gen.templates.keys()))
    
    # Setze die benutzerdefinierte Vorlage
    success = gen.set_template('test')
    print('Set template success:', success)
    print('Current template after set:', gen.current_template)
    
    # Generiere einen Dateinamen
    metadata = {
        "artist": "Test Artist",
        "title": "Test Title"
    }
    
    filename = gen.generate_filename(metadata, '.mp3')
    print('Generated filename:', filename)
    
finally:
    # Räume das temporäre Verzeichnis auf
    shutil.rmtree(temp_dir)