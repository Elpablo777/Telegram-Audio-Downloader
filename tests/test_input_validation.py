"""
Tests für die Eingabevalidierung im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import os

from src.telegram_audio_downloader.input_validation import (
    ValidationType,
    ValidationError,
    ValidationRule,
    ValidationResult,
    ValidationContext,
    InputValidator,
    get_input_validator,
    validate_input,
    validate_form
)


class TestValidationType:
    """Testfälle für die ValidationType-Enumeration."""
    
    def test_validation_type_values(self):
        """Testet die Werte der ValidationType-Enumeration."""
        assert ValidationType.TEXT.value == "text"
        assert ValidationType.NUMBER.value == "number"
        assert ValidationType.EMAIL.value == "email"
        assert ValidationType.URL.value == "url"
        assert ValidationType.PATH.value == "path"
        assert ValidationType.DATE.value == "date"
        assert ValidationType.TIME.value == "time"
        assert ValidationType.PHONE.value == "phone"
        assert ValidationType.CUSTOM.value == "custom"
        assert ValidationType.FILE_SIZE.value == "file_size"
        assert ValidationType.DURATION.value == "duration"
        assert ValidationType.MIME_TYPE.value == "mime_type"


class TestValidationError:
    """Testfälle für die ValidationError-Enumeration."""
    
    def test_validation_error_values(self):
        """Testet die Werte der ValidationError-Enumeration."""
        assert ValidationError.REQUIRED.value == "required"
        assert ValidationError.INVALID_FORMAT.value == "invalid_format"
        assert ValidationError.TOO_SHORT.value == "too_short"
        assert ValidationError.TOO_LONG.value == "too_long"
        assert ValidationError.OUT_OF_RANGE.value == "out_of_range"
        assert ValidationError.NOT_FOUND.value == "not_found"
        assert ValidationError.ALREADY_EXISTS.value == "already_exists"
        assert ValidationError.INVALID_CHOICE.value == "invalid_choice"
        assert ValidationError.CUSTOM.value == "custom"


class TestValidationRule:
    """Testfälle für die ValidationRule-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der ValidationRule-Klasse."""
        rule = ValidationRule(
            field_name="test_field",
            validation_type=ValidationType.TEXT,
            required=True,
            min_length=5,
            max_length=20,
            pattern=r"^[a-z]+$",
            error_message="Invalid format"
        )
        
        assert rule.field_name == "test_field"
        assert rule.validation_type == ValidationType.TEXT
        assert rule.required == True
        assert rule.min_length == 5
        assert rule.max_length == 20
        assert rule.pattern == r"^[a-z]+$"
        assert rule.error_message == "Invalid format"
        assert rule.choices is None
        assert rule.custom_validator is None
        assert rule.allow_empty == False


class TestValidationResult:
    """Testfälle für die ValidationResult-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der ValidationResult-Klasse."""
        result = ValidationResult(
            is_valid=True,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            cleaned_value="cleaned_value",
            field_name="test_field"
        )
        
        assert result.is_valid == True
        assert result.errors == ["Error 1", "Error 2"]
        assert result.warnings == ["Warning 1"]
        assert result.cleaned_value == "cleaned_value"
        assert result.field_name == "test_field"


class TestValidationContext:
    """Testfälle für die ValidationContext-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der ValidationContext-Klasse."""
        data = {"field1": "value1", "field2": "value2"}
        rules = [
            ValidationRule(field_name="field1", validation_type=ValidationType.TEXT),
            ValidationRule(field_name="field2", validation_type=ValidationType.NUMBER)
        ]
        
        context = ValidationContext(
            data=data,
            rules=rules,
            locale="de",
            strict_mode=False
        )
        
        assert context.data == data
        assert context.rules == rules
        assert context.locale == "de"
        assert context.strict_mode == False


class TestInputValidator:
    """Testfälle für die InputValidator-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des InputValidators."""
        validator = InputValidator()
        
        assert validator is not None
        assert isinstance(validator.validators, dict)
        assert isinstance(validator.patterns, dict)
        
        # Überprüfe, ob alle Validierungstypen vorhanden sind
        for validation_type in ValidationType:
            assert validation_type in validator.validators or validation_type.value in validator.validators
    
    def test_validate_text_valid(self):
        """Testet die Validierung von gültigem Text."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="test_field",
            validation_type=ValidationType.TEXT,
            min_length=3,
            max_length=10
        )
        
        context = ValidationContext(data={"test_field": "hello"}, rules=[rule])
        results = validator.validate(context)
        
        assert "test_field" in results
        assert results["test_field"].is_valid == True
        assert results["test_field"].cleaned_value == "hello"
    
    def test_validate_text_too_short(self):
        """Testet die Validierung von zu kurzem Text."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="test_field",
            validation_type=ValidationType.TEXT,
            min_length=10
        )
        
        context = ValidationContext(data={"test_field": "short"}, rules=[rule])
        results = validator.validate(context)
        
        assert "test_field" in results
        assert results["test_field"].is_valid == False
        assert len(results["test_field"].errors) > 0
    
    def test_validate_text_pattern_match(self):
        """Testet die Validierung von Text mit Regex-Muster."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="email_field",
            validation_type=ValidationType.TEXT,
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        
        context = ValidationContext(data={"email_field": "test@example.com"}, rules=[rule])
        results = validator.validate(context)
        
        assert "email_field" in results
        assert results["email_field"].is_valid == True
    
    def test_validate_text_pattern_mismatch(self):
        """Testet die Validierung von Text mit nicht übereinstimmendem Regex-Muster."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="email_field",
            validation_type=ValidationType.TEXT,
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        
        context = ValidationContext(data={"email_field": "invalid-email"}, rules=[rule])
        results = validator.validate(context)
        
        assert "email_field" in results
        assert results["email_field"].is_valid == False
        assert len(results["email_field"].errors) > 0
    
    def test_validate_number_valid(self):
        """Testet die Validierung von gültigen Zahlen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="number_field",
            validation_type=ValidationType.NUMBER,
            min_value=1,
            max_value=100
        )
        
        # Teste Integer
        context = ValidationContext(data={"number_field": "50"}, rules=[rule])
        results = validator.validate(context)
        
        assert "number_field" in results
        assert results["number_field"].is_valid == True
        assert results["number_field"].cleaned_value == 50
        
        # Teste Float
        context = ValidationContext(data={"number_field": "50.5"}, rules=[rule])
        results = validator.validate(context)
        
        assert "number_field" in results
        assert results["number_field"].is_valid == True
        assert results["number_field"].cleaned_value == 50.5
    
    def test_validate_number_out_of_range(self):
        """Testet die Validierung von Zahlen außerhalb des gültigen Bereichs."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="number_field",
            validation_type=ValidationType.NUMBER,
            min_value=10,
            max_value=20
        )
        
        context = ValidationContext(data={"number_field": "5"}, rules=[rule])
        results = validator.validate(context)
        
        assert "number_field" in results
        assert results["number_field"].is_valid == False
        assert len(results["number_field"].errors) > 0
    
    def test_validate_number_invalid_format(self):
        """Testet die Validierung von ungültigen Zahlenformaten."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="number_field",
            validation_type=ValidationType.NUMBER
        )
        
        context = ValidationContext(data={"number_field": "not_a_number"}, rules=[rule])
        results = validator.validate(context)
        
        assert "number_field" in results
        assert results["number_field"].is_valid == False
        assert len(results["number_field"].errors) > 0
    
    def test_validate_email_valid(self):
        """Testet die Validierung von gültigen E-Mail-Adressen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="email_field",
            validation_type=ValidationType.EMAIL
        )
        
        context = ValidationContext(data={"email_field": "test@example.com"}, rules=[rule])
        results = validator.validate(context)
        
        assert "email_field" in results
        assert results["email_field"].is_valid == True
    
    def test_validate_email_invalid(self):
        """Testet die Validierung von ungültigen E-Mail-Adressen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="email_field",
            validation_type=ValidationType.EMAIL
        )
        
        context = ValidationContext(data={"email_field": "invalid-email"}, rules=[rule])
        results = validator.validate(context)
        
        assert "email_field" in results
        assert results["email_field"].is_valid == False
        assert len(results["email_field"].errors) > 0
    
    def test_validate_url_valid(self):
        """Testet die Validierung von gültigen URLs."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="url_field",
            validation_type=ValidationType.URL
        )
        
        context = ValidationContext(data={"url_field": "https://example.com"}, rules=[rule])
        results = validator.validate(context)
        
        assert "url_field" in results
        assert results["url_field"].is_valid == True
    
    def test_validate_url_invalid(self):
        """Testet die Validierung von ungültigen URLs."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="url_field",
            validation_type=ValidationType.URL
        )
        
        context = ValidationContext(data={"url_field": "not-a-url"}, rules=[rule])
        results = validator.validate(context)
        
        assert "url_field" in results
        assert results["url_field"].is_valid == False
        assert len(results["url_field"].errors) > 0
    
    def test_validate_required_field(self):
        """Testet die Validierung von erforderlichen Feldern."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="required_field",
            validation_type=ValidationType.TEXT,
            required=True
        )
        
        # Teste leeres Feld
        context = ValidationContext(data={"required_field": ""}, rules=[rule])
        results = validator.validate(context)
        
        assert "required_field" in results
        assert results["required_field"].is_valid == False
        assert len(results["required_field"].errors) > 0
        
        # Teste fehlendes Feld
        context = ValidationContext(data={}, rules=[rule])
        results = validator.validate(context)
        
        assert "required_field" in results
        assert results["required_field"].is_valid == False
        assert len(results["required_field"].errors) > 0
    
    def test_validate_optional_field(self):
        """Testet die Validierung von optionalen Feldern."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="optional_field",
            validation_type=ValidationType.TEXT,
            required=False
        )
        
        # Teste leeres Feld
        context = ValidationContext(data={"optional_field": ""}, rules=[rule])
        results = validator.validate(context)
        
        assert "optional_field" in results
        assert results["optional_field"].is_valid == True
    
    def test_validate_choice_field_valid(self):
        """Testet die Validierung von Choice-Feldern mit gültiger Auswahl."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="choice_field",
            validation_type=ValidationType.TEXT,
            choices=["option1", "option2", "option3"]
        )
        
        context = ValidationContext(data={"choice_field": "option2"}, rules=[rule])
        results = validator.validate(context)
        
        assert "choice_field" in results
        assert results["choice_field"].is_valid == True
    
    def test_validate_choice_field_invalid(self):
        """Testet die Validierung von Choice-Feldern mit ungültiger Auswahl."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="choice_field",
            validation_type=ValidationType.TEXT,
            choices=["option1", "option2", "option3"]
        )
        
        context = ValidationContext(data={"choice_field": "invalid_option"}, rules=[rule])
        results = validator.validate(context)
        
        assert "choice_field" in results
        assert results["choice_field"].is_valid == False
        assert len(results["choice_field"].errors) > 0
    
    def test_validate_custom_validator(self):
        """Testet die Validierung mit benutzerdefiniertem Validator."""
        validator = InputValidator()
        
        def custom_validator(value):
            if value == "valid":
                return True
            return "Custom validation failed"
        
        rule = ValidationRule(
            field_name="custom_field",
            validation_type=ValidationType.CUSTOM,
            custom_validator=custom_validator
        )
        
        # Teste gültigen Wert
        context = ValidationContext(data={"custom_field": "valid"}, rules=[rule])
        results = validator.validate(context)
        
        assert "custom_field" in results
        assert results["custom_field"].is_valid == True
        
        # Teste ungültigen Wert
        context = ValidationContext(data={"custom_field": "invalid"}, rules=[rule])
        results = validator.validate(context)
        
        assert "custom_field" in results
        assert results["custom_field"].is_valid == False
        assert len(results["custom_field"].errors) > 0
    
    def test_validate_file_size_valid(self):
        """Testet die Validierung von gültigen Dateigrößen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="size_field",
            validation_type=ValidationType.FILE_SIZE
        )
        
        test_cases = [
            ("100B", 100),
            ("1KB", 1024),
            ("1.5MB", int(1.5 * 1024 * 1024)),
            ("2GB", 2 * 1024 * 1024 * 1024)
        ]
        
        for size_str, expected_bytes in test_cases:
            context = ValidationContext(data={"size_field": size_str}, rules=[rule])
            results = validator.validate(context)
            
            assert "size_field" in results
            assert results["size_field"].is_valid == True
            assert results["size_field"].cleaned_value == expected_bytes
    
    def test_validate_file_size_invalid(self):
        """Testet die Validierung von ungültigen Dateigrößen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="size_field",
            validation_type=ValidationType.FILE_SIZE
        )
        
        context = ValidationContext(data={"size_field": "invalid-size"}, rules=[rule])
        results = validator.validate(context)
        
        assert "size_field" in results
        assert results["size_field"].is_valid == False
        assert len(results["size_field"].errors) > 0
    
    def test_validate_duration_valid(self):
        """Testet die Validierung von gültigen Zeitdauern."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="duration_field",
            validation_type=ValidationType.DURATION
        )
        
        # Teste HH:MM:SS Format
        context = ValidationContext(data={"duration_field": "01:30:45"}, rules=[rule])
        results = validator.validate(context)
        
        assert "duration_field" in results
        assert results["duration_field"].is_valid == True
        assert results["duration_field"].cleaned_value == 5445  # 1h 30m 45s in Sekunden
    
    def test_validate_duration_invalid(self):
        """Testet die Validierung von ungültigen Zeitdauern."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="duration_field",
            validation_type=ValidationType.DURATION
        )
        
        context = ValidationContext(data={"duration_field": "invalid-duration"}, rules=[rule])
        results = validator.validate(context)
        
        assert "duration_field" in results
        assert results["duration_field"].is_valid == False
        assert len(results["duration_field"].errors) > 0
    
    def test_validate_mime_type_valid(self):
        """Testet die Validierung von gültigen MIME-Typen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="mime_field",
            validation_type=ValidationType.MIME_TYPE
        )
        
        valid_mimes = [
            "text/plain",
            "application/json",
            "image/png",
            "audio/mpeg"
        ]
        
        for mime in valid_mimes:
            context = ValidationContext(data={"mime_field": mime}, rules=[rule])
            results = validator.validate(context)
            
            assert "mime_field" in results
            assert results["mime_field"].is_valid == True
    
    def test_validate_mime_type_invalid(self):
        """Testet die Validierung von ungültigen MIME-Typen."""
        validator = InputValidator()
        
        rule = ValidationRule(
            field_name="mime_field",
            validation_type=ValidationType.MIME_TYPE
        )
        
        invalid_mimes = [
            "invalid-mime",
            "text/",
            "/plain"
        ]
        
        for mime in invalid_mimes:
            context = ValidationContext(data={"mime_field": mime}, rules=[rule])
            results = validator.validate(context)
            
            assert "mime_field" in results
            assert results["mime_field"].is_valid == False
            assert len(results["mime_field"].errors) > 0
    
    def test_add_custom_validator(self):
        """Testet das Hinzufügen eines benutzerdefinierten Validators."""
        validator = InputValidator()
        
        def test_validator(value, rule, context):
            return ValidationResult(is_valid=True, cleaned_value=value)
        
        validator.add_custom_validator("test_validator", test_validator)
        
        assert "test_validator" in validator.validators
    
    def test_validate_form(self):
        """Testet die Formularvalidierung."""
        validator = InputValidator()
        
        rules = [
            ValidationRule(field_name="name", validation_type=ValidationType.TEXT, required=True, min_length=2),
            ValidationRule(field_name="email", validation_type=ValidationType.EMAIL, required=True),
            ValidationRule(field_name="age", validation_type=ValidationType.NUMBER, min_value=18, max_value=120)
        ]
        
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": "25"
        }
        
        results = validator.validate_form(data, rules)
        
        assert isinstance(results, dict)
        assert len(results) == 3
        assert all(field in results for field in ["name", "email", "age"])
        assert all(results[field].is_valid for field in results)


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_input_validator_singleton(self):
        """Testet, dass der InputValidator als Singleton funktioniert."""
        validator1 = get_input_validator()
        validator2 = get_input_validator()
        
        assert validator1 is validator2
    
    def test_validate_input_global(self):
        """Testet die Eingabevalidierung über die globale Funktion."""
        rule = ValidationRule(
            field_name="test_field",
            validation_type=ValidationType.TEXT,
            required=True
        )
        
        context = ValidationContext(
            data={"test_field": "test_value"},
            rules=[rule]
        )
        
        results = validate_input(context)
        
        assert isinstance(results, dict)
        assert "test_field" in results
        assert results["test_field"].is_valid == True
    
    def test_validate_form_global(self):
        """Testet die Formularvalidierung über die globale Funktion."""
        rules = [
            ValidationRule(field_name="field1", validation_type=ValidationType.TEXT, required=True),
            ValidationRule(field_name="field2", validation_type=ValidationType.NUMBER, required=True)
        ]
        
        data = {
            "field1": "test",
            "field2": "123"
        }
        
        results = validate_form(data, rules)
        
        assert isinstance(results, dict)
        assert len(results) == 2
        assert all(results[field].is_valid for field in results)


if __name__ == "__main__":
    pytest.main([__file__])