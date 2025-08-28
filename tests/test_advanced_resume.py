"""
Tests für die fortgeschrittene Download-Wiederaufnahme.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.telegram_audio_downloader.advanced_resume import (
    AdvancedResumeManager, ResumeInfo, get_resume_manager,
    load_file_resume_state, save_file_resume_state,
    update_file_resume_info, can_resume_download,
    increment_file_retry_count, reset_file_resume_info,
    cleanup_file_resume_info, get_file_progress_info
)


class TestAdvancedResumeManager(unittest.TestCase):
    """Tests für den AdvancedResumeManager."""
    
    def setUp(self):
        """Setzt die Testumgebung auf."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.resume_manager = AdvancedResumeManager(self.test_dir)
        
        # Erstelle eine Testdatei
        self.test_file = self.test_dir / "test_file.mp3"
        self.test_file.write_text("Testinhalt für Prüfsummenberechnung")
    
    def tearDown(self):
        """Räumt die Testumgebung auf."""
        # Lösche temporäre Dateien
        if self.test_file.exists():
            self.test_file.unlink()
        self.test_dir.rmdir()
    
    def test_calculate_checksum(self):
        """Testet die Prüfsummenberechnung."""
        checksum = self.resume_manager.calculate_checksum(self.test_file)
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)  # SHA-256 Prüfsumme
    
    def test_verify_checksum(self):
        """Testet die Prüfsummenverifikation."""
        checksum = self.resume_manager.calculate_checksum(self.test_file)
        self.assertTrue(self.resume_manager.verify_checksum(self.test_file, checksum))
        
        # Teste mit falscher Prüfsumme
        self.assertFalse(self.resume_manager.verify_checksum(self.test_file, "falsche_prüfsumme"))
    
    def test_get_resume_info(self):
        """Testet das Abrufen von Resume-Informationen."""
        file_id = "test_file_001"
        resume_info = self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        
        self.assertIsInstance(resume_info, ResumeInfo)
        self.assertEqual(resume_info.file_id, file_id)
        self.assertEqual(resume_info.file_path, self.test_file)
        self.assertEqual(resume_info.total_bytes, 1024)
        self.assertEqual(resume_info.downloaded_bytes, 0)
    
    def test_update_resume_info(self):
        """Testet das Aktualisieren von Resume-Informationen."""
        file_id = "test_file_002"
        self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        
        self.resume_manager.update_resume_info(file_id, 512)
        
        resume_info = self.resume_manager.resume_data[file_id]
        self.assertEqual(resume_info.downloaded_bytes, 512)
    
    def test_can_resume(self):
        """Testet die Prüfung, ob ein Download wiederaufgenommen werden kann."""
        file_id = "test_file_003"
        
        # Teste mit 0 Bytes heruntergeladen
        self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        self.assertFalse(self.resume_manager.can_resume(file_id))
        
        # Teste mit teilweise heruntergeladenen Bytes
        self.resume_manager.update_resume_info(file_id, 512)
        self.assertTrue(self.resume_manager.can_resume(file_id))
        
        # Teste mit vollständig heruntergeladenen Bytes
        self.resume_manager.update_resume_info(file_id, 1024)
        self.assertFalse(self.resume_manager.can_resume(file_id))
    
    def test_increment_retry_count(self):
        """Testet das Erhöhen des Wiederholungszählers."""
        file_id = "test_file_004"
        self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        
        count1 = self.resume_manager.increment_retry_count(file_id)
        self.assertEqual(count1, 1)
        
        count2 = self.resume_manager.increment_retry_count(file_id)
        self.assertEqual(count2, 2)
    
    def test_reset_resume_info(self):
        """Testet das Zurücksetzen von Resume-Informationen."""
        file_id = "test_file_005"
        self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        self.resume_manager.update_resume_info(file_id, 512)
        self.resume_manager.increment_retry_count(file_id)
        
        self.resume_manager.reset_resume_info(file_id)
        
        resume_info = self.resume_manager.resume_data[file_id]
        self.assertEqual(resume_info.downloaded_bytes, 0)
        self.assertEqual(resume_info.retry_count, 0)
        self.assertIsNone(resume_info.checksum)
    
    def test_cleanup_resume_info(self):
        """Testet das Bereinigen von Resume-Informationen."""
        file_id = "test_file_006"
        self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        
        self.assertIn(file_id, self.resume_manager.resume_data)
        
        self.resume_manager.cleanup_resume_info(file_id)
        
        self.assertNotIn(file_id, self.resume_manager.resume_data)
    
    def test_get_progress_info(self):
        """Testet das Abrufen von Fortschrittsinformationen."""
        file_id = "test_file_007"
        self.resume_manager.get_resume_info(file_id, self.test_file, 1024)
        self.resume_manager.update_resume_info(file_id, 512)
        
        progress_info = self.resume_manager.get_progress_info(file_id)
        
        self.assertIsInstance(progress_info, dict)
        self.assertEqual(progress_info["file_id"], file_id)
        self.assertEqual(progress_info["downloaded_bytes"], 512)
        self.assertEqual(progress_info["total_bytes"], 1024)
        self.assertEqual(progress_info["progress_percent"], 50.0)
        self.assertTrue(progress_info["can_resume"])


class TestResumeFunctions(unittest.TestCase):
    """Tests für die Resume-Funktionen."""
    
    def setUp(self):
        """Setzt die Testumgebung auf."""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Initialisiere den Resume-Manager
        global _resume_manager
        _resume_manager = AdvancedResumeManager(self.test_dir)
    
    def tearDown(self):
        """Räumt die Testumgebung auf."""
        self.test_dir.rmdir()
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_load_file_resume_state(self, mock_manager):
        """Testet das Laden des Resume-Zustands."""
        mock_manager.load_resume_state.return_value = ResumeInfo(
            file_id="test_file_008",
            file_path=Path("test.mp3"),
            total_bytes=1024
        )
        
        resume_info = load_file_resume_state("test_file_008", Path("test.mp3"), 1024)
        
        self.assertIsInstance(resume_info, ResumeInfo)
        mock_manager.load_resume_state.assert_called_once_with("test_file_008", Path("test.mp3"), 1024)
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_save_file_resume_state(self, mock_manager):
        """Testet das Speichern des Resume-Zustands."""
        save_file_resume_state("test_file_009")
        
        mock_manager.save_resume_state.assert_called_once_with("test_file_009")
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_update_file_resume_info(self, mock_manager):
        """Testet das Aktualisieren von Resume-Informationen."""
        update_file_resume_info("test_file_010", 512)
        
        mock_manager.update_resume_info.assert_called_once_with("test_file_010", 512)
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_can_resume_download(self, mock_manager):
        """Testet die Prüfung, ob ein Download wiederaufgenommen werden kann."""
        mock_manager.can_resume.return_value = True
        
        result = can_resume_download("test_file_011")
        
        self.assertTrue(result)
        mock_manager.can_resume.assert_called_once_with("test_file_011")
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_increment_file_retry_count(self, mock_manager):
        """Testet das Erhöhen des Wiederholungszählers."""
        mock_manager.increment_retry_count.return_value = 2
        
        result = increment_file_retry_count("test_file_012")
        
        self.assertEqual(result, 2)
        mock_manager.increment_retry_count.assert_called_once_with("test_file_012")
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_reset_file_resume_info(self, mock_manager):
        """Testet das Zurücksetzen von Resume-Informationen."""
        reset_file_resume_info("test_file_013")
        
        mock_manager.reset_resume_info.assert_called_once_with("test_file_013")
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_cleanup_file_resume_info(self, mock_manager):
        """Testet das Bereinigen von Resume-Informationen."""
        cleanup_file_resume_info("test_file_014")
        
        mock_manager.cleanup_resume_info.assert_called_once_with("test_file_014")
    
    @patch('src.telegram_audio_downloader.advanced_resume._resume_manager')
    def test_get_file_progress_info(self, mock_manager):
        """Testet das Abrufen von Fortschrittsinformationen."""
        mock_manager.get_progress_info.return_value = {
            "file_id": "test_file_015",
            "progress_percent": 50.0
        }
        
        result = get_file_progress_info("test_file_015")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["file_id"], "test_file_015")
        self.assertEqual(result["progress_percent"], 50.0)
        mock_manager.get_progress_info.assert_called_once_with("test_file_015")


if __name__ == '__main__':
    unittest.main()