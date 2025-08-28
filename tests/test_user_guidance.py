"""
Tests für die Benutzerführung im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.telegram_audio_downloader.user_guidance import (
    GuidanceMode,
    GuidanceType,
    GuidanceStep,
    UserProgress,
    GuidanceConfig,
    UserGuidanceManager,
    get_guidance_manager,
    start_tutorial,
    show_hint,
    show_tooltip,
    start_wizard,
    set_guidance_mode,
    show_guidance_overview
)


class TestGuidanceMode:
    """Testfälle für die GuidanceMode-Enumeration."""
    
    def test_guidance_mode_values(self):
        """Testet die Werte der GuidanceMode-Enumeration."""
        assert GuidanceMode.BEGINNER.value == "beginner"
        assert GuidanceMode.INTERMEDIATE.value == "intermediate"
        assert GuidanceMode.ADVANCED.value == "advanced"
        assert GuidanceMode.INTERACTIVE.value == "interactive"


class TestGuidanceType:
    """Testfälle für die GuidanceType-Enumeration."""
    
    def test_guidance_type_values(self):
        """Testet die Werte der GuidanceType-Enumeration."""
        assert GuidanceType.TUTORIAL.value == "tutorial"
        assert GuidanceType.WIZARD.value == "wizard"
        assert GuidanceType.HINT.value == "hint"
        assert GuidanceType.TOOLTIP.value == "tooltip"
        assert GuidanceType.WALKTHROUGH.value == "walkthrough"
        assert GuidanceType.ONBOARDING.value == "onboarding"


class TestGuidanceStep:
    """Testfälle für die GuidanceStep-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der GuidanceStep-Klasse."""
        step = GuidanceStep(
            step_id="test_step",
            title="Test Step",
            description="A test step",
            instructions="Follow these instructions",
            expected_input="test input",
            validation_rules=["rule1", "rule2"],
            help_topic="test_help",
            next_steps=["step2", "step3"],
            prerequisites=["step0"],
            completion_message="Step completed",
            estimated_time=5
        )
        
        assert step.step_id == "test_step"
        assert step.title == "Test Step"
        assert step.description == "A test step"
        assert step.instructions == "Follow these instructions"
        assert step.expected_input == "test input"
        assert step.validation_rules == ["rule1", "rule2"]
        assert step.help_topic == "test_help"
        assert step.next_steps == ["step2", "step3"]
        assert step.prerequisites == ["step0"]
        assert step.completion_message == "Step completed"
        assert step.estimated_time == 5


class TestUserProgress:
    """Testfälle für die UserProgress-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der UserProgress-Klasse."""
        progress = UserProgress(
            user_id="test_user",
            completed_steps=["step1", "step2"],
            current_step="step3",
            progress_percentage=66.67,
            last_activity="2023-01-01 12:00:00",
            preferences={"theme": "dark"},
            completed_tutorials=["tutorial1"]
        )
        
        assert progress.user_id == "test_user"
        assert progress.completed_steps == ["step1", "step2"]
        assert progress.current_step == "step3"
        assert progress.progress_percentage == 66.67
        assert progress.last_activity == "2023-01-01 12:00:00"
        assert progress.preferences == {"theme": "dark"}
        assert progress.completed_tutorials == ["tutorial1"]


class TestGuidanceConfig:
    """Testfälle für die GuidanceConfig-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der GuidanceConfig-Klasse."""
        config = GuidanceConfig(
            mode=GuidanceMode.ADVANCED,
            show_hints=False,
            interactive_tutorials=False,
            auto_advance=True,
            language="de",
            theme="dark",
            enable_tooltips=False,
            show_progress_bar=False,
            skip_completed=False
        )
        
        assert config.mode == GuidanceMode.ADVANCED
        assert config.show_hints == False
        assert config.interactive_tutorials == False
        assert config.auto_advance == True
        assert config.language == "de"
        assert config.theme == "dark"
        assert config.enable_tooltips == False
        assert config.show_progress_bar == False
        assert config.skip_completed == False


class TestUserGuidanceManager:
    """Testfälle für die UserGuidanceManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des UserGuidanceManagers."""
        manager = UserGuidanceManager()
        
        assert manager is not None
        assert hasattr(manager, 'console')
        assert hasattr(manager, 'config')
        assert isinstance(manager.user_progress, dict)
        assert isinstance(manager.guidance_steps, dict)
        assert isinstance(manager.tutorials, dict)
        assert isinstance(manager.wizards, dict)
        
        # Überprüfe, ob Standard-Tutorials initialisiert wurden
        assert "onboarding" in manager.tutorials
        assert "advanced_features" in manager.tutorials
    
    def test_initialization_with_config(self):
        """Testet die Initialisierung mit benutzerdefinierter Konfiguration."""
        config = GuidanceConfig(mode=GuidanceMode.ADVANCED)
        manager = UserGuidanceManager(config)
        
        assert manager.config.mode == GuidanceMode.ADVANCED
    
    def test_start_tutorial_valid(self):
        """Testet das Starten eines gültigen Tutorials."""
        manager = UserGuidanceManager()
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            manager.start_tutorial("onboarding")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Starten des Tutorials: {e}")
    
    def test_start_tutorial_invalid(self):
        """Testet das Starten eines ungültigen Tutorials."""
        manager = UserGuidanceManager()
        
        # Dies sollte ohne Exception ausgeführt werden (zeigt Fehlermeldung)
        try:
            manager.start_tutorial("invalid_tutorial")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Starten eines ungültigen Tutorials: {e}")
    
    def test_show_hint(self):
        """Testet das Anzeigen eines Hinweises."""
        manager = UserGuidanceManager()
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            manager.show_hint("test_topic", "test context")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen eines Hinweises: {e}")
    
    def test_show_tooltip(self):
        """Testet das Anzeigen eines Tooltips."""
        manager = UserGuidanceManager()
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            manager.show_tooltip("test_element", "test description")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen eines Tooltips: {e}")
    
    def test_start_wizard_valid(self):
        """Testet das Starten eines gültigen Assistenten."""
        manager = UserGuidanceManager()
        
        # Füge einen Test-Wizard hinzu
        test_steps = [
            GuidanceStep(
                step_id="wizard_step_1",
                title="Wizard Step 1",
                description="First wizard step",
                instructions="Follow instructions"
            )
        ]
        manager.wizards["test_wizard"] = test_steps
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            results = manager.start_wizard("test_wizard")
            assert isinstance(results, dict)
        except Exception as e:
            pytest.fail(f"Fehler beim Starten des Assistenten: {e}")
    
    def test_start_wizard_invalid(self):
        """Testet das Starten eines ungültigen Assistenten."""
        manager = UserGuidanceManager()
        
        # Dies sollte ohne Exception ausgeführt werden (zeigt Fehlermeldung)
        try:
            results = manager.start_wizard("invalid_wizard")
            assert isinstance(results, dict)
        except Exception as e:
            pytest.fail(f"Fehler beim Starten eines ungültigen Assistenten: {e}")
    
    def test_get_user_progress(self):
        """Testet das Abrufen des Benutzerfortschritts."""
        manager = UserGuidanceManager()
        
        # Für einen neuen Benutzer sollte None zurückgegeben werden
        progress = manager.get_user_progress("new_user")
        assert progress is None
        
        # Starte ein Tutorial, um den Fortschritt zu erstellen
        manager.start_tutorial("onboarding", "test_user")
        
        # Jetzt sollte der Fortschritt vorhanden sein
        progress = manager.get_user_progress("test_user")
        assert progress is not None
        assert isinstance(progress, UserProgress)
        assert progress.user_id == "test_user"
    
    def test_reset_user_progress(self):
        """Testet das Zurücksetzen des Benutzerfortschritts."""
        manager = UserGuidanceManager()
        
        # Starte ein Tutorial, um den Fortschritt zu erstellen
        manager.start_tutorial("onboarding", "test_user")
        
        # Überprüfe, ob Fortschritt vorhanden ist
        progress = manager.get_user_progress("test_user")
        assert progress is not None
        assert len(progress.completed_steps) > 0
        
        # Setze den Fortschritt zurück
        manager.reset_user_progress("test_user")
        
        # Überprüfe, ob der Fortschritt zurückgesetzt wurde
        progress = manager.get_user_progress("test_user")
        assert progress is not None
        assert len(progress.completed_steps) == 0
    
    def test_set_guidance_mode(self):
        """Testet das Setzen des Führungungsmodus."""
        manager = UserGuidanceManager()
        
        # Setze den Modus auf Advanced
        manager.set_guidance_mode(GuidanceMode.ADVANCED)
        
        assert manager.config.mode == GuidanceMode.ADVANCED
    
    def test_show_guidance_overview(self):
        """Testet das Anzeigen der Führungungsübersicht."""
        manager = UserGuidanceManager()
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            manager.show_guidance_overview()
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Führungungsübersicht: {e}")
    
    def test_execute_tutorial_steps(self):
        """Testet die Ausführung von Tutorial-Schritten."""
        manager = UserGuidanceManager()
        
        # Erstelle Test-Schritte
        steps = [
            GuidanceStep(
                step_id="test_step_1",
                title="Test Step 1",
                description="First test step",
                instructions="Do something",
                completion_message="Step 1 completed"
            ),
            GuidanceStep(
                step_id="test_step_2",
                title="Test Step 2",
                description="Second test step",
                instructions="Do something else",
                completion_message="Step 2 completed"
            )
        ]
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            manager._execute_tutorial_steps(steps, "test_user", "test_tutorial")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler bei der Ausführung von Tutorial-Schritten: {e}")
    
    def test_show_guidance_step(self):
        """Testet das Anzeigen eines Führungungsschritts."""
        manager = UserGuidanceManager()
        
        # Erstelle einen Test-Schritt
        step = GuidanceStep(
            step_id="test_step",
            title="Test Step",
            description="A test step",
            instructions="Follow these instructions",
            expected_input="test input",
            estimated_time=5,
            help_topic="test_help",
            completion_message="Step completed"
        )
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            manager._show_guidance_step(step)
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen eines Führungungsschritts: {e}")


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_guidance_manager_singleton(self):
        """Testet, dass der UserGuidanceManager als Singleton funktioniert."""
        manager1 = get_guidance_manager()
        manager2 = get_guidance_manager()
        
        assert manager1 is manager2
    
    def test_start_tutorial_global(self):
        """Testet das Starten eines Tutorials über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden
        try:
            start_tutorial("onboarding")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Starten eines Tutorials über die globale Funktion: {e}")
    
    def test_show_hint_global(self):
        """Testet das Anzeigen eines Hinweises über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden
        try:
            show_hint("test_topic", "test context")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen eines Hinweises über die globale Funktion: {e}")
    
    def test_show_tooltip_global(self):
        """Testet das Anzeigen eines Tooltips über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden
        try:
            show_tooltip("test_element", "test description")
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen eines Tooltips über die globale Funktion: {e}")
    
    def test_start_wizard_global(self):
        """Testet das Starten eines Assistenten über die globale Funktion."""
        # Füge einen Test-Wizard hinzu
        manager = get_guidance_manager()
        test_steps = [
            GuidanceStep(
                step_id="global_wizard_step_1",
                title="Global Wizard Step 1",
                description="First global wizard step",
                instructions="Follow instructions"
            )
        ]
        manager.wizards["global_test_wizard"] = test_steps
        
        # Dies sollte ohne Exception ausgeführt werden
        try:
            results = start_wizard("global_test_wizard")
            assert isinstance(results, dict)
        except Exception as e:
            pytest.fail(f"Fehler beim Starten eines Assistenten über die globale Funktion: {e}")
    
    def test_set_guidance_mode_global(self):
        """Testet das Setzen des Führungungsmodus über die globale Funktion."""
        # Setze den Modus auf Intermediate
        set_guidance_mode(GuidanceMode.INTERMEDIATE)
        
        manager = get_guidance_manager()
        assert manager.config.mode == GuidanceMode.INTERMEDIATE
    
    def test_show_guidance_overview_global(self):
        """Testet das Anzeigen der Führungungsübersicht über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden
        try:
            show_guidance_overview()
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Führungungsübersicht über die globale Funktion: {e}")


if __name__ == "__main__":
    pytest.main([__file__])