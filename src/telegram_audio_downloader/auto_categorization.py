"""
Automatische Kategorisierung für den Telegram Audio Downloader.
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path

from .models import AudioFile
from .logging_config import get_logger

logger = get_logger(__name__)


class AutoCategorizer:
    """Klasse zur automatischen Kategorisierung von Audiodateien."""
    
    def __init__(self):
        """Initialisiert den AutoCategorizer."""
        self.category_keywords = {
            "classical": ["classical", "klassik", "orchestra", "symphony", "mozart", "beethoven", "bach"],
            "jazz": ["jazz", "swing", "blues", "improvisation"],
            "rock": ["rock", "metal", "punk", "grunge"],
            "pop": ["pop", "chart", "top 40"],
            "electronic": ["electronic", "techno", "house", "edm", "dance"],
            "hiphop": ["hip hop", "rap", "urban"],
            "country": ["country", "western", "folk"],
            "reggae": ["reggae", "bob marley"],
            "latin": ["latin", "salsa", "reggaeton"],
            "world": ["world", "ethnic", "tribal"]
        }
        
        # Kompiliere die Regex-Muster für bessere Performance
        self.compiled_patterns = {
            category: [re.compile(keyword, re.IGNORECASE) for keyword in keywords]
            for category, keywords in self.category_keywords.items()
        }
    
    def categorize_file(self, audio_file: AudioFile) -> str:
        """
        Kategorisiert eine Audiodatei basierend auf ihren Metadaten.
        
        Args:
            audio_file: AudioFile-Objekt zur Kategorisierung
            
        Returns:
            Kategoriename als String
        """
        try:
            # Sammle alle verfügbaren Textdaten
            text_data = []
            
            if audio_file.title:
                text_data.append(audio_file.title)
                
            if audio_file.performer:
                text_data.append(audio_file.performer)
                
            if audio_file.file_name:
                text_data.append(audio_file.file_name)
            
            # Kombiniere alle Textdaten
            combined_text = " ".join(text_data).lower()
            
            # Prüfe auf Übereinstimmungen mit den Kategorien
            category_scores = {}
            
            for category, patterns in self.compiled_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = pattern.findall(combined_text)
                    score += len(matches)
                category_scores[category] = score
            
            # Finde die Kategorie mit der höchsten Punktzahl
            if any(score > 0 for score in category_scores.values()):
                best_category = max(category_scores, key=category_scores.get)
                logger.info(f"Datei {audio_file.file_name} kategorisiert als '{best_category}'")
                return best_category
            else:
                logger.info(f"Keine klare Kategorie für Datei {audio_file.file_name} gefunden, verwende 'unclassified'")
                return "unclassified"
                
        except Exception as e:
            logger.error(f"Fehler bei der Kategorisierung der Datei {audio_file.file_name}: {e}")
            return "unclassified"
    
    def categorize_by_folder_structure(self, base_path: str) -> Dict[str, List[str]]:
        """
        Kategorisiert Dateien basierend auf der Ordnerstruktur.
        
        Args:
            base_path: Basispfad zur Musikbibliothek
            
        Returns:
            Dictionary mit Kategorien als Schlüssel und Dateilisten als Werte
        """
        categorized_files = {}
        
        try:
            base_path_obj = Path(base_path)
            
            # Durchlaufe alle Unterverzeichnisse
            for folder in base_path_obj.iterdir():
                if folder.is_dir():
                    category = folder.name.lower()
                    files = [str(f) for f in folder.iterdir() if f.is_file() and f.suffix.lower() in [".mp3", ".flac", ".m4a", ".wav", ".ogg"]]
                    categorized_files[category] = files
                    
            logger.info(f"Kategorisierung nach Ordnerstruktur abgeschlossen für {len(categorized_files)} Kategorien")
            return categorized_files
            
        except Exception as e:
            logger.error(f"Fehler bei der Kategorisierung nach Ordnerstruktur: {e}")
            return categorized_files
    
    def create_category_folders(self, base_path: str, categories: List[str]) -> None:
        """
        Erstellt Ordner für die angegebenen Kategorien.
        
        Args:
            base_path: Basispfad zur Musikbibliothek
            categories: Liste der Kategorienamen
        """
        try:
            base_path_obj = Path(base_path)
            
            for category in categories:
                category_path = base_path_obj / category
                category_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Ordner für Kategorie '{category}' erstellt: {category_path}")
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Kategorieordner: {e}")

# Globale Instanz
_auto_categorizer: Optional[AutoCategorizer] = None

def get_auto_categorizer() -> AutoCategorizer:
    """
    Gibt die globale Instanz des AutoCategorizers zurück.
    
    Returns:
        Instanz von AutoCategorizer
    """
    global _auto_categorizer
    if _auto_categorizer is None:
        _auto_categorizer = AutoCategorizer()
    return _auto_categorizer

def categorize_audio_file(audio_file: AudioFile) -> str:
    """
    Kategorisiert eine Audiodatei.
    
    Args:
        audio_file: AudioFile-Objekt zur Kategorisierung
        
    Returns:
        Kategoriename als String
    """
    categorizer = get_auto_categorizer()
    return categorizer.categorize_file(audio_file)

def categorize_by_folder(base_path: str) -> Dict[str, List[str]]:
    """
    Kategorisiert Dateien basierend auf der Ordnerstruktur.
    
    Args:
        base_path: Basispfad zur Musikbibliothek
        
    Returns:
        Dictionary mit Kategorien als Schlüssel und Dateilisten als Werte
    """
    categorizer = get_auto_categorizer()
    return categorizer.categorize_by_folder_structure(base_path)