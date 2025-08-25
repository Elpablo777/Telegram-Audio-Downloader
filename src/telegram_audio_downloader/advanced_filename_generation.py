"""
Erweiterte Dateinamen-Generierung für den Telegram Audio Downloader.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from string import Template

from .error_handling import handle_error
from .file_error_handler import handle_file_error, with_file_error_handling
from .utils import sanitize_filename

logger = logging.getLogger(__name__)

# Standard templates for filenames
DEFAULT_TEMPLATES = {
    "simple": "$artist - $title",
    "detailed": "$artist - $title ($year)",
    "numbered": "$artist - $track_number. $title",
    "full": "$artist - $album ($year) - $track_number. $title"
}

# Available placeholders
AVAILABLE_PLACEHOLDERS = {
    "title", "artist", "album", "year", "genre", "track_number", 
    "disc_number", "date", "composer", "performer", "duration",
    "bitrate", "sample_rate", "channels", "file_size", "file_extension",
    "message_id", "group_name", "group_id", "download_date", "counter"
}

class FilenameTemplate:
    """Class for managing filename templates."""
    
    def __init__(self, template_string: str):
        """
        Initializes a filename template.
        
        Args:
            template_string: Template as string with placeholders
        """
        self.template_string = template_string
        self.template = Template(template_string)
        self.placeholders = self._extract_placeholders()
        
    def _extract_placeholders(self) -> set:
        """
        Extracts placeholders from the template.
        
        Returns:
            Set of placeholders in the template
        """
        # Finde alle Platzhalter im Format $platzhalter oder ${platzhalter}
        pattern = r'\$(\w+)|\$\{(\w+)\}'
        matches = re.findall(pattern, self.template_string)
        
        # Extrahiere die Platzhalter aus den Matches
        placeholders = set()
        for match in matches:
            # match ist ein Tupel, eines der beiden Elemente ist der Platzhalter
            # In each tuple, one element is empty, the other contains the placeholder
            placeholder = match[0] if match[0] else match[1]
            placeholders.add(placeholder)
            
        return placeholders
        
    def validate_placeholders(self) -> bool:
        """
        Validates that all placeholders in the template are valid.
        
        Returns:
            True if all placeholders are valid
        """
        return self.placeholders.issubset(AVAILABLE_PLACEHOLDERS)
        
    def render(self, metadata: Dict[str, Any], counter: int = 1) -> str:
        """
        Renders the template with the given metadata.
        
        Args:
            metadata: Metadata for placeholders
            counter: Counter for numbered filenames
            
        Returns:
            Rendered filename
        """
        # Erstelle ein Dictionary mit allen verfügbaren Platzhaltern
        template_data = {
            "counter": str(counter).zfill(3),  # 001, 002, 003, ...
            "download_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # Add the metadata
        template_data.update(metadata)
        
        # Add derived fields
        if "date" in template_data and template_data["date"]:
            try:
                # Versuche, das Jahr aus dem Datum zu extrahieren
                if isinstance(template_data["date"], str):
                    if "T" in template_data["date"]:
                        date_obj = datetime.fromisoformat(template_data["date"].split("T")[0])
                    else:
                        date_obj = datetime.fromisoformat(template_data["date"])
                    template_data["year"] = str(date_obj.year)
                elif isinstance(template_data["date"], (int, float)):
                    # Wenn es bereits ein Jahr ist
                    template_data["year"] = str(int(template_data["date"]))
            except (ValueError, TypeError):
                # Falls das Datum nicht im ISO-Format ist, versuche es als Jahr
                if isinstance(template_data["date"], str) and len(template_data["date"]) == 4 and template_data["date"].isdigit():
                    template_data["year"] = template_data["date"]
        
        # Fill missing placeholders with empty strings
        for placeholder in self.placeholders:
            if placeholder not in template_data:
                template_data[placeholder] = ""
                
        # Debug-Ausgabe
        logger.debug(f"Template data: {template_data}")
        logger.debug(f"Placeholders: {self.placeholders}")
        logger.debug(f"Template string: {self.template_string}")
                
        # Rendere die Vorlage
        try:
            filename = self.template.substitute(template_data)
            return filename
        except KeyError as e:
            logger.warning(f"Fehlender Platzhalter in Vorlage: {e}")
            # Fallback: Use safe_substitute
            return self.template.safe_substitute(template_data)

class AdvancedFilenameGenerator:
    """Advanced filename generation with customizable templates."""
    
    def __init__(self, download_dir: Union[str, Path]):
        """
        Initializes the advanced filename generator.
        
        Args:
            download_dir: Download directory
        """
        self.download_dir = Path(download_dir)
        self.templates = DEFAULT_TEMPLATES.copy()
        self.current_template = "detailed"
        self.counter = 1
        self.used_filenames = set()
        
    def add_template(self, name: str, template: str) -> bool:
        """
        Adds a new template.
        
        Args:
            name: Template name
            template: Template string
            
        Returns:
            True if template was successfully added
        """
        try:
            # Validate the template
            template_obj = FilenameTemplate(template)
            if not template_obj.validate_placeholders():
                logger.error(f"Invalid placeholders in template '{name}': {template}")
                return False
                
            self.templates[name] = template
            return True
        except Exception as e:
            logger.error(f"Error adding template '{name}': {e}")
            return False
            
    def set_template(self, name: str) -> bool:
        """
        Sets the current template.
        
        Args:
            name: Template name
            
        Returns:
            True if template was successfully set
        """
        if name in self.templates:
            self.current_template = name
            return True
        logger.error(f"Template '{name}' not found")
        return False
        
    def generate_filename(self, metadata: Dict[str, Any], 
                         file_extension: str = ".mp3",
                         template_name: Optional[str] = None) -> str:
        """
        Generates a filename based on metadata.
        
        Args:
            metadata: Metadata for filename generation
            file_extension: File extension
            template_name: Name of template to use (optional)
            
        Returns:
            Generated filename
        """
        # Bestimme die zu verwendende Vorlage
        template_key = template_name if template_name and template_name in self.templates else self.current_template
        template_string = self.templates[template_key]
        
        # Erstelle die Vorlagen-Objekt
        template = FilenameTemplate(template_string)
        
        # Rendere den Dateinamen
        base_name = template.render(metadata, self.counter)
        self.counter += 1
        
        # Füge die Dateiendung hinzu
        if not base_name.endswith(file_extension):
            filename = f"{base_name}{file_extension}"
        else:
            filename = base_name
            
        # Bereinige den Dateinamen
        filename = sanitize_filename(filename)
        
        # Vermeide Kollisionen
        filename = self._avoid_collision(filename)
        
        # Füge den Dateinamen zu den verwendeten Dateinamen hinzu
        self.used_filenames.add(filename)
        
        return filename
        
    def _avoid_collision(self, filename: str) -> str:
        """
        Vermeidet Kollisionen von Dateinamen.
        
        Args:
            filename: Ursprünglicher Dateiname
            
        Returns:
            Eindeutiger Dateiname
        """
        # Prüfe sowohl auf Datei-System-Ebene als auch in der internen Liste
        if not (self.download_dir / filename).exists() and filename not in self.used_filenames:
            return filename
            
        # Extrahiere den Basisnamen und die Erweiterung
        path_obj = Path(filename)
        stem = path_obj.stem
        suffix = path_obj.suffix
        
        # Versuche, eine Nummer an den Dateinamen anzuhängen
        counter = 1
        while True:
            new_filename = f"{stem}_{counter}{suffix}"
            if not (self.download_dir / new_filename).exists() and new_filename not in self.used_filenames:
                return new_filename
            counter += 1
            # Sicherheitscheck, um Endlosschleifen zu vermeiden
            if counter > 1000:
                # Fallback: Verwende einen Zeitstempel
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{stem}_{timestamp}{suffix}"
                
    def get_available_templates(self) -> Dict[str, str]:
        """
        Returns available templates.
        
        Returns:
            Dictionary of template names and template strings
        """
        return self.templates.copy()
    
    def reset_counter(self) -> None:
        """Resets the filename counter."""
        self.counter = 1
        
    def _make_filename_unique(self, filename: str, file_extension: str) -> str:
        """
        Makes a filename unique by adding a counter if necessary.
        
        Args:
            filename: Base filename
            file_extension: File extension
            
        Returns:
            Unique filename
        """
        full_filename = f"{filename}{file_extension}"
        counter = 1
        
        # Wenn der Dateiname bereits verwendet wird, füge einen Zähler hinzu
        while full_filename in self.used_filenames:
            full_filename = f"{filename}_{counter}{file_extension}"
            counter += 1
            
        self.used_filenames.add(full_filename)
        return full_filename

def get_filename_generator(download_dir: Union[str, Path]) -> AdvancedFilenameGenerator:
    """
    Returns an instance of AdvancedFilenameGenerator.
    
    Args:
        download_dir: Download directory
        
    Returns:
        AdvancedFilenameGenerator instance
    """
    return AdvancedFilenameGenerator(download_dir)

# Globale Instanz des erweiterten Dateinamen-Generators
_advanced_filename_generator: Optional[AdvancedFilenameGenerator] = None

def get_advanced_filename_generator(download_dir: Union[str, Path] = "downloads") -> AdvancedFilenameGenerator:
    """
    Gibt die globale Instanz des erweiterten Dateinamen-Generators zurück.
    
    Args:
        download_dir: Verzeichnis für Downloads
        
    Returns:
        Instanz des AdvancedFilenameGenerator
    """
    global _advanced_filename_generator
    if _advanced_filename_generator is None:
        _advanced_filename_generator = AdvancedFilenameGenerator(download_dir)
    return _advanced_filename_generator

# Hilfsfunktionen für die Verwendung außerhalb der Klasse
@with_file_error_handling()
def generate_filename_from_metadata(
    metadata: Dict[str, Any], 
    file_extension: str = ".mp3",
    template_name: Optional[str] = None,
    download_dir: Union[str, Path] = "downloads"
) -> str:
    """
    Generiert einen Dateinamen aus Metadaten mit erweiterten Funktionen.
    
    Args:
        metadata: Metadaten für die Dateinamen-Generierung
        file_extension: Dateiendung
        template_name: Name der zu verwendenden Vorlage (optional)
        download_dir: Verzeichnis für Downloads
        
    Returns:
        Generierter Dateiname
    """
    generator = get_advanced_filename_generator(download_dir)
    return generator.generate_filename(metadata, file_extension, template_name)