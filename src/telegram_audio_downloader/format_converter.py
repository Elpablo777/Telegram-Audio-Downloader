"""
Automatische Formatkonvertierung für den Telegram Audio Downloader.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any
import shutil
import sys

# Prüfe die Python-Version und passe den pydub-Import entsprechend an
PYDUB_AVAILABLE = False
AudioSegment = None

try:
    # Versuche, pydub zu importieren
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None
except Exception as e:
    # Behandle spezifische Kompatibilitätsprobleme mit Python 3.13
    if "audioop" in str(e) or "pyaudioop" in str(e):
        # Kompatibilitätsproblem mit Python 3.13
        PYDUB_AVAILABLE = False
        AudioSegment = None
        logging.warning("pydub ist nicht mit der aktuellen Python-Version kompatibel. "
                       "Bitte verwenden Sie Python 3.12 oder älter für die Formatkonvertierung.")
    else:
        PYDUB_AVAILABLE = False
        AudioSegment = None
        logging.warning(f"pydub konnte nicht importiert werden: {e}")

from .error_handling import handle_error, FileOperationError, ConfigurationError
from .file_error_handler import handle_file_error, with_file_error_handling

logger = logging.getLogger(__name__)

# Unterstützte Zielformate
SUPPORTED_FORMATS = {
    "mp3": {"extension": ".mp3", "format": "mp3"},
    "m4a": {"extension": ".m4a", "format": "mp4"},
    "flac": {"extension": ".flac", "format": "flac"},
    "opus": {"extension": ".opus", "format": "opus"}
}

class FormatConverter:
    """Klasse zur automatischen Konvertierung von Audiodateien in verschiedene Formate."""
    
    def __init__(self, temp_dir: Union[str, Path] = "temp"):
        """
        Initialisiert den Formatkonverter.
        
        Args:
            temp_dir: Verzeichnis für temporäre Dateien
        """
        if not PYDUB_AVAILABLE:
            # Prüfe, ob es ein Kompatibilitätsproblem mit Python 3.13 ist
            if sys.version_info >= (3, 13):
                raise ConfigurationError(
                    "pydub ist nicht mit Python 3.13 kompatibel. "
                    "Bitte verwenden Sie Python 3.12 oder älter für die Formatkonvertierung, "
                    "oder warten Sie auf ein pydub-Update, das Python 3.13 unterstützt."
                )
            else:
                raise ConfigurationError(
                    "pydub ist nicht installiert. Bitte installieren Sie es mit: pip install pydub"
                )
        
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
    @with_file_error_handling()
    def convert_audio_file(self, source_file: Union[str, Path], 
                          target_format: str, 
                          target_file: Optional[Union[str, Path]] = None,
                          **conversion_options: Any) -> Path:
        """
        Konvertiert eine Audiodatei in ein anderes Format.
        
        Args:
            source_file: Pfad zur Quelldatei
            target_format: Zielformat (mp3, m4a, flac, opus)
            target_file: Optionaler Pfad zur Zieldatei (wird automatisch generiert, wenn nicht angegeben)
            **conversion_options: Zusätzliche Optionen für die Konvertierung
                bitrate: Bitrate für die Ausgabedatei (z.B. "192k")
                sample_rate: Samplerate für die Ausgabedatei (z.B. 44100)
                channels: Anzahl der Kanäle (1 für Mono, 2 für Stereo)
                
        Returns:
            Pfad zur konvertierten Datei
            
        Raises:
            FileOperationError: Bei Konvertierungsfehlern
            ConfigurationError: Bei ungültigen Formatangaben
        """
        source_file = Path(source_file)
        
        # Prüfe, ob die Quelldatei existiert
        if not source_file.exists():
            raise FileOperationError(f"Quelldatei nicht gefunden: {source_file}")
        
        # Prüfe, ob das Zielformat unterstützt wird
        if target_format.lower() not in SUPPORTED_FORMATS:
            raise ConfigurationError(
                f"Nicht unterstütztes Zielformat: {target_format}. "
                f"Unterstützte Formate: {', '.join(SUPPORTED_FORMATS.keys())}"
            )
        
        # Bestimme den Zielpfad
        if target_file is None:
            target_file = source_file.parent / f"{source_file.stem}.{target_format.lower()}"
        else:
            target_file = Path(target_file)
        
        # Wenn Quelle und Ziel identisch sind, keine Konvertierung notwendig
        if source_file == target_file:
            logger.info(f"Quelle und Ziel sind identisch: {source_file}")
            return source_file
        
        try:
            # Lade die Audiodatei
            logger.debug(f"Lade Audiodatei: {source_file}")
            audio = AudioSegment.from_file(str(source_file))
            
            # Wende Konvertierungsoptionen an
            audio = self._apply_conversion_options(audio, **conversion_options)
            
            # Konvertiere und speichere die Datei
            format_info = SUPPORTED_FORMATS[target_format.lower()]
            logger.debug(f"Konvertiere in {target_format.upper()}: {target_file}")
            
            # Spezifische Parameter für verschiedene Formate
            export_kwargs = {}
            if target_format.lower() == "mp3":
                export_kwargs["format"] = "mp3"
                if "bitrate" in conversion_options:
                    export_kwargs["bitrate"] = conversion_options["bitrate"]
            elif target_format.lower() == "m4a":
                export_kwargs["format"] = "mp4"
            elif target_format.lower() == "flac":
                export_kwargs["format"] = "flac"
            elif target_format.lower() == "opus":
                export_kwargs["format"] = "opus"
                if "bitrate" in conversion_options:
                    export_kwargs["bitrate"] = conversion_options["bitrate"]
            
            # Exportiere die Datei
            audio.export(str(target_file), **export_kwargs)
            
            logger.info(f"Konvertierung abgeschlossen: {source_file} -> {target_file}")
            return target_file
            
        except Exception as e:
            raise FileOperationError(
                f"Fehler bei der Konvertierung von {source_file} nach {target_format.upper()}: {e}"
            )
    
    def _apply_conversion_options(self, audio: AudioSegment, **options: Any) -> AudioSegment:
        """
        Wendet Konvertierungsoptionen auf ein AudioSegment an.
        
        Args:
            audio: AudioSegment zum Verarbeiten
            **options: Konvertierungsoptionen
            
        Returns:
            Verarbeitetes AudioSegment
        """
        # Samplerate anpassen
        if "sample_rate" in options and options["sample_rate"] is not None:
            audio = audio.set_frame_rate(options["sample_rate"])
        
        # Kanäle anpassen
        if "channels" in options and options["channels"] is not None:
            if options["channels"] == 1:
                audio = audio.set_channels(1)
            elif options["channels"] == 2:
                audio = audio.set_channels(2)
        
        return audio
    
    @with_file_error_handling()
    async def convert_audio_file_async(self, source_file: Union[str, Path], 
                                     target_format: str, 
                                     target_file: Optional[Union[str, Path]] = None,
                                     **conversion_options: Any) -> Path:
        """
        Asynchrone Konvertierung einer Audiodatei in ein anderes Format.
        
        Args:
            source_file: Pfad zur Quelldatei
            target_format: Zielformat (mp3, m4a, flac, opus)
            target_file: Optionaler Pfad zur Zieldatei (wird automatisch generiert, wenn nicht angegeben)
            **conversion_options: Zusätzliche Optionen für die Konvertierung
                
        Returns:
            Pfad zur konvertierten Datei
        """
        # Führe die Konvertierung in einem Thread-Pool-Executor aus, um den Event-Loop nicht zu blockieren
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self.convert_audio_file, 
            source_file, 
            target_format, 
            target_file,
            **conversion_options
        )
        return result
    
    @with_file_error_handling()
    def batch_convert(self, file_mappings: Dict[Union[str, Path], Dict[str, Any]]) -> Dict[Union[str, Path], Path]:
        """
        Konvertiert mehrere Dateien in einem Batch.
        
        Args:
            file_mappings: Dictionary mit Quelldateien als Schlüssel und Konvertierungsoptionen als Werte
                Beispiel: {
                    "source1.mp3": {"target_format": "flac", "bitrate": "320k"},
                    "source2.wav": {"target_format": "mp3", "sample_rate": 44100}
                }
                
        Returns:
            Dictionary mit Quelldateien als Schlüssel und Pfaden zu konvertierten Dateien als Werte
        """
        results = {}
        errors = {}
        
        for source_file, options in file_mappings.items():
            try:
                target_format = options.pop("target_format", "mp3")
                target_file = options.pop("target_file", None)
                
                converted_file = self.convert_audio_file(
                    source_file, target_format, target_file, **options
                )
                results[source_file] = converted_file
                
            except Exception as e:
                errors[source_file] = str(e)
                logger.error(f"Fehler bei der Konvertierung von {source_file}: {e}")
        
        # Melde Fehler, falls welche aufgetreten sind
        if errors:
            logger.warning(f"{len(errors)} von {len(file_mappings)} Dateien konnten nicht konvertiert werden")
        
        return results
    
    @with_file_error_handling()
    async def batch_convert_async(self, file_mappings: Dict[Union[str, Path], Dict[str, Any]]) -> Dict[Union[str, Path], Path]:
        """
        Asynchrone Batch-Konvertierung mehrerer Dateien.
        
        Args:
            file_mappings: Dictionary mit Quelldateien als Schlüssel und Konvertierungsoptionen als Werte
                
        Returns:
            Dictionary mit Quelldateien als Schlüssel und Pfaden zu konvertierten Dateien als Werte
        """
        results = {}
        errors = {}
        
        # Erstelle Tasks für alle Konvertierungen
        tasks = []
        for source_file, options in file_mappings.items():
            target_format = options.pop("target_format", "mp3")
            target_file = options.pop("target_file", None)
            
            task = asyncio.create_task(
                self.convert_audio_file_async(source_file, target_format, target_file, **options)
            )
            tasks.append((source_file, task))
        
        # Warte auf Abschluss aller Tasks
        for source_file, task in tasks:
            try:
                converted_file = await task
                results[source_file] = converted_file
            except Exception as e:
                errors[source_file] = str(e)
                logger.error(f"Fehler bei der Konvertierung von {source_file}: {e}")
        
        # Melde Fehler, falls welche aufgetreten sind
        if errors:
            logger.warning(f"{len(errors)} von {len(file_mappings)} Dateien konnten nicht konvertiert werden")
        
        return results
    
    def cleanup_temp_files(self) -> None:
        """Löscht temporäre Dateien."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                logger.debug("Temporäre Dateien gelöscht")
        except Exception as e:
            logger.warning(f"Fehler beim Löschen temporärer Dateien: {e}")

# Globale Instanz des Formatkonverters
_format_converter: Optional[FormatConverter] = None

def get_format_converter(temp_dir: Union[str, Path] = "temp") -> FormatConverter:
    """
    Gibt die globale Instanz des Formatkonverters zurück.
    
    Args:
        temp_dir: Verzeichnis für temporäre Dateien
        
    Returns:
        Instanz des FormatConverter
    """
    global _format_converter
    if _format_converter is None:
        _format_converter = FormatConverter(temp_dir)
    return _format_converter

# Hilfsfunktionen für die Verwendung außerhalb der Klasse
@with_file_error_handling()
def convert_audio_file(source_file: Union[str, Path], 
                      target_format: str, 
                      target_file: Optional[Union[str, Path]] = None,
                      **conversion_options: Any) -> Path:
    """
    Konvertiert eine Audiodatei in ein anderes Format.
    
    Args:
        source_file: Pfad zur Quelldatei
        target_format: Zielformat (mp3, m4a, flac, opus)
        target_file: Optionaler Pfad zur Zieldatei (wird automatisch generiert, wenn nicht angegeben)
        **conversion_options: Zusätzliche Optionen für die Konvertierung
            
    Returns:
        Pfad zur konvertierten Datei
    """
    converter = get_format_converter()
    return converter.convert_audio_file(source_file, target_format, target_file, **conversion_options)

@with_file_error_handling()
async def convert_audio_file_async(source_file: Union[str, Path], 
                                 target_format: str, 
                                 target_file: Optional[Union[str, Path]] = None,
                                 **conversion_options: Any) -> Path:
    """
    Asynchrone Konvertierung einer Audiodatei in ein anderes Format.
    
    Args:
        source_file: Pfad zur Quelldatei
        target_format: Zielformat (mp3, m4a, flac, opus)
        target_file: Optionaler Pfad zur Zieldatei (wird automatisch generiert, wenn nicht angegeben)
        **conversion_options: Zusätzliche Optionen für die Konvertierung
            
    Returns:
        Pfad zur konvertierten Datei
    """
    converter = get_format_converter()
    return await converter.convert_audio_file_async(source_file, target_format, target_file, **conversion_options)