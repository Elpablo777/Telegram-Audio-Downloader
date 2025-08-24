"""
Test-Suite für die fortgeschrittene Download-Wiederaufnahme.
"""

import unittest
import sys
from pathlib import Path

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.test_advanced_resume import TestAdvancedResumeManager, TestResumeFunctions


def create_resume_test_suite():
    """Erstellt eine Test-Suite für die Resume-Funktionalität."""
    suite = unittest.TestSuite()
    
    # Füge alle Testfälle für den AdvancedResumeManager hinzu
    suite.addTest(unittest.makeSuite(TestAdvancedResumeManager))
    
    # Füge alle Testfälle für die Resume-Funktionen hinzu
    suite.addTest(unittest.makeSuite(TestResumeFunctions))
    
    return suite


def run_resume_tests():
    """Führt alle Resume-Tests aus."""
    suite = create_resume_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == '__main__':
    result = run_resume_tests()
    # Exit mit einem Code ungleich 0, wenn Tests fehlschlagen
    sys.exit(not result.wasSuccessful())