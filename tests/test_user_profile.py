"""
Tests für die Benutzerprofilierung im Telegram Audio Downloader.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from src.telegram_audio_downloader.user_profile import (
    UserProfile,
    UserProfileManager,
    get_profile_manager,
    create_user_profile,
    load_user_profile,
    save_user_profile,
    set_current_user_profile,
    get_current_user_profile,
    update_user_preference,
    get_user_preference
)


class TestUserProfile:
    """Testfälle für die UserProfile-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der UserProfile-Klasse."""
        profile = UserProfile(user_id="test_user_123")
        
        assert profile.user_id == "test_user_123"
        assert profile.username is None
        assert profile.email is None
        assert isinstance(profile.created_at, datetime)
        assert profile.last_login is None
        assert profile.preferences == {}
        assert profile.download_history == []
        assert profile.favorite_groups == []
        assert profile.custom_categories == {}
        assert profile.accessibility_settings == {}
        assert profile.keyboard_shortcuts == {}
        assert profile.language == "en"
        assert profile.theme == "default"
        assert profile.download_path is None
        assert profile.max_concurrent_downloads == 3
        assert profile.download_quality == "high"
        assert profile.auto_categorize == True
        assert profile.notifications_enabled == True
        assert profile.notification_methods == ["system"]
        assert profile.privacy_settings == {}
        assert profile.statistics == {}
    
    def test_initialization_with_parameters(self):
        """Testet die Initialisierung mit benutzerdefinierten Parametern."""
        profile = UserProfile(
            user_id="test_user_456",
            username="testuser",
            email="test@example.com",
            language="de",
            theme="dark",
            max_concurrent_downloads=5
        )
        
        assert profile.user_id == "test_user_456"
        assert profile.username == "testuser"
        assert profile.email == "test@example.com"
        assert profile.language == "de"
        assert profile.theme == "dark"
        assert profile.max_concurrent_downloads == 5


class TestUserProfileManager:
    """Testfälle für die UserProfileManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des UserProfileManagers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            assert manager is not None
            assert hasattr(manager, 'profiles_dir')
            assert hasattr(manager, 'current_profile')
            assert manager.current_profile is None
            assert manager.profiles_dir == temp_dir
    
    def test_create_profile(self):
        """Testet das Erstellen eines Benutzerprofils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            profile = manager.create_profile(
                user_id="test_create_user",
                username="testcreator",
                email="creator@example.com"
            )
            
            assert profile is not None
            assert profile.user_id == "test_create_user"
            assert profile.username == "testcreator"
            assert profile.email == "creator@example.com"
            
            # Überprüfe, ob die Profildatei erstellt wurde
            profile_path = manager._get_profile_path("test_create_user")
            assert profile_path.exists()
    
    def test_load_profile(self):
        """Testet das Laden eines Benutzerprofils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            created_profile = manager.create_profile(
                user_id="test_load_user",
                username="testloader",
                email="loader@example.com"
            )
            
            # Lade das Profil
            loaded_profile = manager.load_profile("test_load_user")
            
            assert loaded_profile is not None
            assert loaded_profile.user_id == "test_load_user"
            assert loaded_profile.username == "testloader"
            assert loaded_profile.email == "loader@example.com"
            assert isinstance(loaded_profile.created_at, datetime)
    
    def test_load_nonexistent_profile(self):
        """Testet das Laden eines nicht existierenden Profils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Versuche, ein nicht existierendes Profil zu laden
            profile = manager.load_profile("nonexistent_user")
            
            assert profile is None
    
    def test_save_profile(self):
        """Testet das Speichern eines Benutzerprofils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            profile = UserProfile(user_id="test_save_user")
            profile.username = "testsaver"
            profile.preferences["test_key"] = "test_value"
            
            # Speichere das Profil
            manager.save_profile(profile)
            
            # Lade das Profil erneut
            loaded_profile = manager.load_profile("test_save_user")
            
            assert loaded_profile is not None
            assert loaded_profile.username == "testsaver"
            assert loaded_profile.preferences["test_key"] == "test_value"
    
    def test_delete_profile(self):
        """Testet das Löschen eines Benutzerprofils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_delete_user")
            
            # Überprüfe, ob das Profil existiert
            assert manager.load_profile("test_delete_user") is not None
            
            # Lösche das Profil
            result = manager.delete_profile("test_delete_user")
            
            assert result == True
            
            # Überprüfe, ob das Profil gelöscht wurde
            assert manager.load_profile("test_delete_user") is None
    
    def test_delete_nonexistent_profile(self):
        """Testet das Löschen eines nicht existierenden Profils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Versuche, ein nicht existierendes Profil zu löschen
            result = manager.delete_profile("nonexistent_user")
            
            assert result == False
    
    def test_list_profiles(self):
        """Testet das Auflisten von Benutzerprofilen."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle mehrere Profile
            manager.create_profile(user_id="user1")
            manager.create_profile(user_id="user2")
            manager.create_profile(user_id="user3")
            
            # Liste die Profile auf
            profiles = manager.list_profiles()
            
            assert len(profiles) == 3
            # Die Profile sind gehasht, daher können wir nicht die genauen IDs überprüfen
    
    def test_set_and_get_current_profile(self):
        """Testet das Setzen und Abrufen des aktuellen Profils."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            profile = UserProfile(user_id="test_current_user")
            
            # Setze das aktuelle Profil
            manager.set_current_profile(profile)
            
            # Hole das aktuelle Profil
            current_profile = manager.get_current_profile()
            
            assert current_profile is not None
            assert current_profile.user_id == "test_current_user"
            assert current_profile.last_login is not None
    
    def test_update_preference(self):
        """Testet das Aktualisieren einer Benutzereinstellung."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_pref_user")
            
            # Aktualisiere eine Einstellung
            result = manager.update_preference("test_pref_user", "theme", "dark")
            
            assert result == True
            
            # Überprüfe die Einstellung
            value = manager.get_preference("test_pref_user", "theme")
            assert value == "dark"
    
    def test_get_preference_with_default(self):
        """Testet das Abrufen einer Benutzereinstellung mit Standardwert."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_default_user")
            
            # Hole eine nicht existierende Einstellung mit Standardwert
            value = manager.get_preference("test_default_user", "nonexistent_key", "default_value")
            assert value == "default_value"
    
    def test_add_to_download_history(self):
        """Testet das Hinzufügen zu der Download-Historie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_history_user")
            
            # Füge einen Download zur Historie hinzu
            download_info = {
                "file_name": "test_file.mp3",
                "file_size": 1024,
                "duration": 180
            }
            
            result = manager.add_to_download_history("test_history_user", download_info)
            assert result == True
            
            # Hole die Download-Historie
            history = manager.get_download_history("test_history_user")
            assert len(history) == 1
            assert history[0]["file_name"] == "test_file.mp3"
            assert "timestamp" in history[0]
    
    def test_add_favorite_group(self):
        """Testet das Hinzufügen einer Telegram-Gruppe zu den Favoriten."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_fav_user")
            
            # Füge eine Gruppe zu den Favoriten hinzu
            result = manager.add_favorite_group("test_fav_user", "group_123")
            assert result == True
            
            # Hole die Favoritengruppen
            favorites = manager.get_favorite_groups("test_fav_user")
            assert len(favorites) == 1
            assert "group_123" in favorites
    
    def test_remove_favorite_group(self):
        """Testet das Entfernen einer Telegram-Gruppe aus den Favoriten."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_remove_fav_user")
            
            # Füge eine Gruppe zu den Favoriten hinzu
            manager.add_favorite_group("test_remove_fav_user", "group_123")
            
            # Entferne die Gruppe aus den Favoriten
            result = manager.remove_favorite_group("test_remove_fav_user", "group_123")
            assert result == True
            
            # Hole die Favoritengruppen
            favorites = manager.get_favorite_groups("test_remove_fav_user")
            assert len(favorites) == 0
    
    def test_update_statistics(self):
        """Testet das Aktualisieren von Benutzerstatistiken."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = UserProfileManager(profiles_dir=temp_dir)
            
            # Erstelle ein Profil
            manager.create_profile(user_id="test_stats_user")
            
            # Aktualisiere eine Statistik
            result = manager.update_statistics("test_stats_user", "total_downloads", 42)
            assert result == True
            
            # Hole die Statistiken
            stats = manager.get_statistics("test_stats_user")
            assert stats["total_downloads"] == 42


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_profile_manager_singleton(self):
        """Testet, dass der UserProfileManager als Singleton funktioniert."""
        manager1 = get_profile_manager()
        manager2 = get_profile_manager()
        
        assert manager1 is manager2
    
    def test_create_user_profile_global(self):
        """Testet das Erstellen eines Benutzerprofils über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager, um das temporäre Verzeichnis zu verwenden
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Erstelle ein Profil
                profile = UserProfile(user_id="global_test_user")
                mock_manager.create_profile.return_value = profile
                
                created_profile = create_user_profile("global_test_user")
                
                assert created_profile is not None
                assert created_profile.user_id == "global_test_user"
                mock_manager.create_profile.assert_called_once_with("global_test_user", None, None)
    
    def test_load_user_profile_global(self):
        """Testet das Laden eines Benutzerprofils über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager, um das temporäre Verzeichnis zu verwenden
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Lade ein Profil
                profile = UserProfile(user_id="global_load_user")
                mock_manager.load_profile.return_value = profile
                
                loaded_profile = load_user_profile("global_load_user")
                
                assert loaded_profile is not None
                assert loaded_profile.user_id == "global_load_user"
                mock_manager.load_profile.assert_called_once_with("global_load_user")
    
    def test_save_user_profile_global(self):
        """Testet das Speichern eines Benutzerprofils über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Speichere ein Profil
                profile = UserProfile(user_id="global_save_user")
                save_user_profile(profile)
                
                mock_manager.save_profile.assert_called_once_with(profile)
    
    def test_set_current_user_profile_global(self):
        """Testet das Setzen des aktuellen Benutzerprofils über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Setze das aktuelle Profil
                profile = UserProfile(user_id="global_current_user")
                set_current_user_profile(profile)
                
                mock_manager.set_current_profile.assert_called_once_with(profile)
    
    def test_get_current_user_profile_global(self):
        """Testet das Abrufen des aktuellen Benutzerprofils über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Hole das aktuelle Profil
                profile = UserProfile(user_id="global_get_current_user")
                mock_manager.get_current_profile.return_value = profile
                
                current_profile = get_current_user_profile()
                
                assert current_profile is not None
                assert current_profile.user_id == "global_get_current_user"
                mock_manager.get_current_profile.assert_called_once()
    
    def test_update_user_preference_global(self):
        """Testet das Aktualisieren einer Benutzereinstellung über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Aktualisiere eine Einstellung
                mock_manager.update_preference.return_value = True
                
                result = update_user_preference("global_pref_user", "theme", "light")
                
                assert result == True
                mock_manager.update_preference.assert_called_once_with("global_pref_user", "theme", "light")
    
    def test_get_user_preference_global(self):
        """Testet das Abrufen einer Benutzereinstellung über die globale Funktion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Patch den ProfileManager
            with patch('src.telegram_audio_downloader.user_profile.UserProfileManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                
                # Hole eine Einstellung
                mock_manager.get_preference.return_value = "dark"
                
                value = get_user_preference("global_get_pref_user", "theme", "light")
                
                assert value == "dark"
                mock_manager.get_preference.assert_called_once_with("global_get_pref_user", "theme", "light")


if __name__ == "__main__":
    pytest.main([__file__])