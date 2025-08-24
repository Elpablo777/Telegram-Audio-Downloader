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

# Standardvorlagen für Dateinamen
DEFAULT_TEMPLATES = {
    "simple": "$artist - $title",
    "detailed": "$artist - $title ($year)",
    "numbered": "$artist - $track_number. $title",
    "full": "$artist - $album ($year) - $track_number. $title"
}

# Verfügbare Platzhalter
AVAILABLE_PLACEHOLDERS = {
    "title", "artist", "album", "year", "genre", "track_number", 
    "disc_number", "date", "composer", "performer", "duration",
    "bitrate", "sample_rate", "channels", "file_size", "file_extension",
    "message_id", "group_name", "group_id", "download_date", "counter"
}

class FilenameTemplate:
    """Klasse zur Verwaltung von Dateinamen-Vorlagen."""
    
    def __init__(self, template_string: str):
        """
        Initialisiert eine Dateinamen-Vorlage.
        
        Args:
            template_string: Vorlage als String mit Platzhaltern
        """
        self.template_string = template_string
        self.template = Template(template_string)
        self.placeholders = self._extract_placeholders()
        
    def _extract_placeholders(self) -> set:
        """
        Extrahiert die Platzhalter aus der Vorlage.
        
        Returns:
            Menge der Platzhalter in der Vorlage
        """
        # Finde alle Platzhalter im Format $platzhalter oder ${platzhalter}
        pattern = r'\$(\w+)|\$\{(\w+)\}'
        matches = re.findall(pattern, self.template_string)
        
        # Extrahiere die Platzhalter aus den Matches
        placeholders = set()
        for match in matches:
            # match ist ein Tupel, eines der beiden Elemente ist der Platzhalter
            # In jedem Tupel ist eines der Elemente leer, das andere enthält den Platzhalter
            placeholder = match[0] if match[0] else match[1]
            placeholders.add(placeholder)
            
        return placeholders
        
    def validate_placeholders(self) -> bool:
        """
        Validiert, ob alle Platzhalter in der Vorlage gültig sind.
        
        Returns:
            True, wenn alle Platzhalter gültig sind
        """
        return self.placeholders.issubset(AVAILABLE_PLACEHOLDERS)
        
    def render(self, metadata: Dict[str, Any], counter: int = 1) -> str:
        """
        Rendert die Vorlage mit den gegebenen Metadaten.
        
        Args:
            metadata: Metadaten für die Platzhalter
            counter: Zähler für nummerierte Dateinamen
            
        Returns:
            Gerenderter Dateiname
        """
        # Erstelle ein Dictionary mit allen verfügbaren Platzhaltern
        template_data = {
            "counter": str(counter).zfill(3),  # 001, 002, 003, ...
            "download_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # Füge die Metadaten hinzu
        template_data.update(metadata)
        
        # Füge abgeleitete Felder hinzu
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
        
        # Fülle fehlende Platzhalter mit leeren Strings
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
            # Fallback: Verwende safe_substitute
            return self.template.safe_substitute(template_data)

class AdvancedFilenameGenerator:
    """Erweiterte Dateinamen-Generierung mit anpassbaren Vorlagen."""
    
    def __init__(self, download_dir: Union[str, Path]):
        """
        Initialisiert den erweiterten Dateinamen-Generator.
        
        Args:
            download_dir: Verzeichnis für Downloads
        """
        self.download_dir = Path(download_dir)
        self.templates = DEFAULT_TEMPLATES.copy()
        self.current_template = "detailed"
        self.counter = 1
        self.used_filenames = set()
        
    def add_template(self, name: str, template: str) -> bool:
        """
        Fügt eine neue Vorlage hinzu.
        
        Args:
            name: Name der Vorlage
            template: Vorlagen-String
            
        Returns:
            True, wenn die Vorlage erfolgreich hinzugefügt wurde
        """
        try:
            # Validiere die Vorlage
            template_obj = FilenameTemplate(template)
            if not template_obj.validate_placeholders():
                logger.error(f"Ungültige Platzhalter in Vorlage '{name}': {template}")
                return False
                
            self.templates[name] = template
            return True
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Vorlage '{name}': {e}")
            return False
            
    def set_template(self, name: str) -> bool:
        """
        Setzt die aktuelle Vorlage.
        
        Args:
            name: Name der Vorlage
            
        Returns:
            True, wenn die Vorlage erfolgreich gesetzt wurde
        """
        if name in self.templates:
            self.current_template = name
            return True
        logger.error(f"Vorlage '{name}' nicht gefunden")
        return False
        
    def generate_filename(self, metadata: Dict[str, Any], 
                         file_extension: str = ".mp3",
                         template_name: Optional[str] = None) -> str:
        """
        Generiert einen Dateinamen basierend auf den Metadaten.
        
        Args:
            metadata: Metadaten für die Dateinamen-Generierung
            file_extension: Dateiendung
            template_name: Name der zu verwendenden Vorlage (optional)
            
        Returns:
            Generierter Dateiname
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