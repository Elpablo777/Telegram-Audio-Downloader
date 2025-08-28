"""
Eingabevalidierung für den Telegram Audio Downloader.
"""

from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime
import os

from .logging_config import get_logger
from .i18n import _

logger = get_logger(__name__)


class ValidationType(Enum):
    """Enumeration der Validierungstypen."""
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    URL = "url"
    PATH = "path"
    DATE = "date"
    TIME = "time"
    PHONE = "phone"
    CUSTOM = "custom"
    FILE_SIZE = "file_size"
    DURATION = "duration"
    MIME_TYPE = "mime_type"


class ValidationError(Enum):
    """Enumeration der Validierungsfehler."""
    REQUIRED = "required"
    INVALID_FORMAT = "invalid_format"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    OUT_OF_RANGE = "out_of_range"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    INVALID_CHOICE = "invalid_choice"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """Datenklasse für eine Validierungsregel."""
    field_name: str
    validation_type: ValidationType
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None  # Regex-Muster
    choices: Optional[List[Any]] = None
    custom_validator: Optional[Callable] = None
    error_message: str = ""
    allow_empty: bool = False


@dataclass
class ValidationResult:
    """Datenklasse für ein Validierungsergebnis."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cleaned_value: Any = None
    field_name: str = ""


@dataclass
class ValidationContext:
    """Datenklasse für den Validierungskontext."""
    data: Dict[str, Any]
    rules: List[ValidationRule]
    locale: str = "en"
    strict_mode: bool = True  # Bei True werden Warnungen als Fehler behandelt


class InputValidator:
    """Klasse zur Validierung von Benutzereingaben."""
    
    def __init__(self):
        """Initialisiert den InputValidator."""
        self.validators = {
            ValidationType.TEXT: self._validate_text,
            ValidationType.NUMBER: self._validate_number,
            ValidationType.EMAIL: self._validate_email,
            ValidationType.URL: self._validate_url,
            ValidationType.PATH: self._validate_path,
            ValidationType.DATE: self._validate_date,
            ValidationType.TIME: self._validate_time,
            ValidationType.PHONE: self._validate_phone,
            ValidationType.FILE_SIZE: self._validate_file_size,
            ValidationType.DURATION: self._validate_duration,
            ValidationType.MIME_TYPE: self._validate_mime_type,
            ValidationType.CUSTOM: self._validate_custom
        }
        
        # Standard-Regex-Muster
        self.patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
            "phone": r"^\+?[\d\s\-\(\)]{7,15}$",
            "file_size": r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)$",
            "duration": r"^(\d+):([0-5]\d):([0-5]\d)$"  # HH:MM:SS
        }
    
    def validate(self, context: ValidationContext) -> Dict[str, ValidationResult]:
        """
        Validiert die Daten basierend auf den Regeln im Kontext.
        
        Args:
            context: Validierungskontext mit Daten und Regeln
            
        Returns:
            Dictionary mit Validierungsergebnissen für jedes Feld
        """
        results = {}
        
        for rule in context.rules:
            field_name = rule.field_name
            value = context.data.get(field_name)
            
            # Prüfe, ob das Feld erforderlich ist
            if rule.required and (value is None or value == ""):
                results[field_name] = ValidationResult(
                    is_valid=False,
                    errors=[_("field_required").format(field=field_name)],
                    field_name=field_name
                )
                continue
            
            # Überspringe leere Felder, wenn sie erlaubt sind
            if not rule.required and (value is None or value == "") and rule.allow_empty:
                results[field_name] = ValidationResult(
                    is_valid=True,
                    cleaned_value=value,
                    field_name=field_name
                )
                continue
            
            # Führe die Validierung durch
            result = self._validate_field(value, rule, context)
            results[field_name] = result
        
        return results
    
    def _validate_field(self, value: Any, rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """
        Validiert ein einzelnes Feld.
        
        Args:
            value: Der zu validierende Wert
            rule: Die Validierungsregel
            context: Der Validierungskontext
            
        Returns:
            Validierungsergebnis
        """
        # Erstelle das Ergebnisobjekt
        result = ValidationResult(
            is_valid=True,
            field_name=rule.field_name
        )
        
        # Konvertiere den Wert in einen String, falls nötig
        if value is not None and not isinstance(value, str):
            value = str(value)
        
        # Prüfe benutzerdefinierte Validierungsfunktion
        if rule.custom_validator:
            try:
                custom_result = rule.custom_validator(value)
                if custom_result is not True:
                    result.is_valid = False
                    if isinstance(custom_result, str):
                        result.errors.append(custom_result)
                    else:
                        result.errors.append(_("custom_validation_failed").format(field=rule.field_name))
                    return result
            except Exception as e:
                result.is_valid = False
                result.errors.append(_("custom_validation_error").format(field=rule.field_name, error=str(e)))
                return result
        
        # Führe die typenspezifische Validierung durch
        if rule.validation_type in self.validators:
            validator_func = self.validators[rule.validation_type]
            validator_result = validator_func(value, rule, context)
            
            # Kombiniere die Ergebnisse
            result.is_valid = validator_result.is_valid
            result.errors.extend(validator_result.errors)
            result.warnings.extend(validator_result.warnings)
            result.cleaned_value = validator_result.cleaned_value
        
        # Prüfe zusätzliche Regeln
        if result.is_valid and value is not None:
            # Längenprüfung
            if rule.min_length is not None and len(value) < rule.min_length:
                result.is_valid = False
                result.errors.append(
                    _("field_too_short").format(field=rule.field_name, min_length=rule.min_length)
                )
            
            if rule.max_length is not None and len(value) > rule.max_length:
                result.is_valid = False
                result.errors.append(
                    _("field_too_long").format(field=rule.field_name, max_length=rule.max_length)
                )
            
            # Choice-Prüfung
            if rule.choices and value not in rule.choices:
                result.is_valid = False
                result.errors.append(
                    _("invalid_choice").format(field=rule.field_name, choices=", ".join(str(c) for c in rule.choices))
                )
        
        return result
    
    def _validate_text(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Texteingaben."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        # Prüfe Regex-Muster
        if rule.pattern:
            try:
                if not re.match(rule.pattern, value):
                    result.is_valid = False
                    result.errors.append(
                        rule.error_message or _("invalid_text_format").format(field=rule.field_name)
                    )
            except re.error as e:
                result.is_valid = False
                result.errors.append(_("invalid_regex_pattern").format(error=str(e)))
        
        return result
    
    def _validate_number(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Zahleneingaben."""
        result = ValidationResult(is_valid=True)
        
        if value is None:
            return result
        
        try:
            # Versuche, den Wert in eine Zahl zu konvertieren
            if '.' in value:
                num_value = float(value)
                result.cleaned_value = num_value
            else:
                num_value = int(value)
                result.cleaned_value = num_value
            
            # Prüfe Wertebereich
            if rule.min_value is not None and num_value < rule.min_value:
                result.is_valid = False
                result.errors.append(
                    _("number_too_small").format(field=rule.field_name, min_value=rule.min_value)
                )
            
            if rule.max_value is not None and num_value > rule.max_value:
                result.is_valid = False
                result.errors.append(
                    _("number_too_large").format(field=rule.field_name, max_value=rule.max_value)
                )
                
        except ValueError:
            result.is_valid = False
            result.errors.append(_("invalid_number_format").format(field=rule.field_name))
        
        return result
    
    def _validate_email(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert E-Mail-Adressen."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        email_pattern = self.patterns["email"]
        if not re.match(email_pattern, value):
            result.is_valid = False
            result.errors.append(_("invalid_email_format").format(field=rule.field_name))
        
        return result
    
    def _validate_url(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert URLs."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        url_pattern = self.patterns["url"]
        if not re.match(url_pattern, value):
            result.is_valid = False
            result.errors.append(_("invalid_url_format").format(field=rule.field_name))
        
        return result
    
    def _validate_path(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Dateipfade."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        # Prüfe, ob der Pfad existiert (abhängig von der Konfiguration)
        if context.strict_mode:
            if not os.path.exists(value):
                result.is_valid = False
                result.errors.append(_("path_not_found").format(field=rule.field_name, path=value))
        
        return result
    
    def _validate_date(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Datumsangaben."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        # Versuche verschiedene Datumsformate
        date_formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%m/%d/%Y",
            "%Y.%m.%d"
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt)
                result.cleaned_value = parsed_date
                break
            except ValueError:
                continue
        
        if parsed_date is None:
            result.is_valid = False
            result.errors.append(_("invalid_date_format").format(field=rule.field_name))
        
        return result
    
    def _validate_time(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Zeitangaben."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        # Versuche verschiedene Zeitformate
        time_formats = [
            "%H:%M",
            "%H:%M:%S",
            "%I:%M %p",
            "%I:%M:%S %p"
        ]
        
        parsed_time = None
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(value, fmt).time()
                result.cleaned_value = parsed_time
                break
            except ValueError:
                continue
        
        if parsed_time is None:
            result.is_valid = False
            result.errors.append(_("invalid_time_format").format(field=rule.field_name))
        
        return result
    
    def _validate_phone(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Telefonnummern."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        phone_pattern = self.patterns["phone"]
        if not re.match(phone_pattern, value):
            result.is_valid = False
            result.errors.append(_("invalid_phone_format").format(field=rule.field_name))
        
        return result
    
    def _validate_file_size(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Dateigrößenangaben."""
        result = ValidationResult(is_valid=True)
        
        if value is None:
            return result
        
        size_pattern = self.patterns["file_size"]
        match = re.match(size_pattern, value.strip())
        
        if not match:
            result.is_valid = False
            result.errors.append(_("invalid_file_size_format").format(field=rule.field_name))
            return result
        
        # Konvertiere in Bytes
        size_value = float(match.group(1))
        size_unit = match.group(2).upper()
        
        unit_multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4
        }
        
        bytes_value = size_value * unit_multipliers.get(size_unit, 1)
        result.cleaned_value = int(bytes_value)
        
        return result
    
    def _validate_duration(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert Zeitdauerangaben."""
        result = ValidationResult(is_valid=True)
        
        if value is None:
            return result
        
        duration_pattern = self.patterns["duration"]
        match = re.match(duration_pattern, value.strip())
        
        if not match:
            result.is_valid = False
            result.errors.append(_("invalid_duration_format").format(field=rule.field_name))
            return result
        
        # Konvertiere in Sekunden
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        result.cleaned_value = total_seconds
        
        return result
    
    def _validate_mime_type(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert MIME-Typen."""
        result = ValidationResult(is_valid=True, cleaned_value=value)
        
        if value is None:
            return result
        
        # Einfache Prüfung auf gültiges MIME-Type-Format
        mime_pattern = r"^[a-z]+/[a-z0-9._+-]+$"
        if not re.match(mime_pattern, value.lower()):
            result.is_valid = False
            result.errors.append(_("invalid_mime_type_format").format(field=rule.field_name))
        
        return result
    
    def _validate_custom(self, value: Optional[str], rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        """Validiert benutzerdefinierte Eingaben."""
        # Diese Methode wird für CUSTOM-Validierungstypen verwendet
        # Die eigentliche Validierung erfolgt in der custom_validator-Funktion der Regel
        return ValidationResult(is_valid=True, cleaned_value=value)
    
    def add_custom_validator(self, name: str, validator: Callable):
        """
        Fügt einen benutzerdefinierten Validator hinzu.
        
        Args:
            name: Name des Validators
            validator: Validator-Funktion
        """
        self.validators[name] = validator
        logger.debug(f"Benutzerdefinierter Validator hinzugefügt: {name}")
    
    def validate_form(self, data: Dict[str, Any], rules: List[ValidationRule], 
                      locale: str = "en", strict_mode: bool = True) -> Dict[str, ValidationResult]:
        """
        Validiert ein komplettes Formular.
        
        Args:
            data: Formulardaten
            rules: Validierungsregeln
            locale: Sprache
            strict_mode: Strikter Modus
            
        Returns:
            Validierungsergebnisse
        """
        context = ValidationContext(
            data=data,
            rules=rules,
            locale=locale,
            strict_mode=strict_mode
        )
        
        return self.validate(context)


# Globale Instanz
_input_validator: Optional[InputValidator] = None


def get_input_validator() -> InputValidator:
    """
    Gibt die globale Instanz des InputValidators zurück.
    
    Returns:
        Instanz von InputValidator
    """
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


def validate_input(context: ValidationContext) -> Dict[str, ValidationResult]:
    """
    Validiert die Eingaben basierend auf dem Kontext.
    
    Args:
        context: Validierungskontext
        
    Returns:
        Validierungsergebnisse
    """
    validator = get_input_validator()
    return validator.validate(context)


def validate_form(data: Dict[str, Any], rules: List[ValidationRule], 
                  locale: str = "en", strict_mode: bool = True) -> Dict[str, ValidationResult]:
    """
    Validiert ein komplettes Formular.
    
    Args:
        data: Formulardaten
        rules: Validierungsregeln
        locale: Sprache
        strict_mode: Strikter Modus
        
    Returns:
        Validierungsergebnisse
    """
    validator = get_input_validator()
    return validator.validate_form(data, rules, locale, strict_mode)


# Deutsche Übersetzungen für Eingabevalidierung
INPUT_VALIDATION_TRANSLATIONS_DE = {
    "field_required": "Das Feld '{field}' ist erforderlich",
    "custom_validation_failed": "Benutzerdefinierte Validierung für Feld '{field}' fehlgeschlagen",
    "custom_validation_error": "Fehler bei benutzerdefinierter Validierung für Feld '{field}': {error}",
    "field_too_short": "Das Feld '{field}' ist zu kurz (mindestens {min_length} Zeichen)",
    "field_too_long": "Das Feld '{field}' ist zu lang (maximal {max_length} Zeichen)",
    "invalid_choice": "Ungültige Auswahl für Feld '{field}'. Erlaubt: {choices}",
    "invalid_text_format": "Ungültiges Format für Feld '{field}'",
    "invalid_regex_pattern": "Ungültiges Regex-Muster: {error}",
    "number_too_small": "Der Wert für Feld '{field}' ist zu klein (mindestens {min_value})",
    "number_too_large": "Der Wert für Feld '{field}' ist zu groß (maximal {max_value})",
    "invalid_number_format": "Ungültiges Zahlenformat für Feld '{field}'",
    "invalid_email_format": "Ungültiges E-Mail-Format für Feld '{field}'",
    "invalid_url_format": "Ungültiges URL-Format für Feld '{field}'",
    "path_not_found": "Pfad für Feld '{field}' nicht gefunden: {path}",
    "invalid_date_format": "Ungültiges Datumsformat für Feld '{field}'",
    "invalid_time_format": "Ungültiges Zeitformat für Feld '{field}'",
    "invalid_phone_format": "Ungültiges Telefonnummernformat für Feld '{field}'",
    "invalid_file_size_format": "Ungültiges Dateigrößenformat für Feld '{field}'",
    "invalid_duration_format": "Ungültiges Zeitdauerformat für Feld '{field}'",
    "invalid_mime_type_format": "Ungültiges MIME-Type-Format für Feld '{field}'",
}