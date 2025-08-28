"""
Datenbank-API für den Telegram Audio Downloader.

Abstraktionsschicht mit:
- RESTful API
- GraphQL-Interface
- Datenvalidierung
- Zugriffskontrolle
"""

import json
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from functools import wraps
import sqlite3

from flask import Flask, request, jsonify, Blueprint
from flask_graphql import GraphQLView
import graphene
from graphene import ObjectType, String, Int, Float, DateTime, List as GrapheneList, Field

from .models import AudioFile, TelegramGroup, db
from .database_validation import get_database_validator
from .logging_config import get_logger

logger = get_logger(__name__)


# GraphQL-Schema
class AudioFileType(ObjectType):
    """GraphQL-Typ für AudioFile."""
    id = Int()
    file_id = String()
    file_name = String()
    file_size = Int()
    duration = Int()
    title = String()
    performer = String()
    group_id = Int()
    downloaded_at = DateTime()
    status = String()
    error_message = String()
    download_attempts = Int()


class TelegramGroupType(ObjectType):
    """GraphQL-Typ für TelegramGroup."""
    id = Int()
    group_id = Int()
    title = String()
    username = String()


class Query(ObjectType):
    """GraphQL-Abfrage-Klasse."""
    
    # AudioFile-Abfragen
    audio_file = Field(AudioFileType, file_id=String())
    audio_files = GrapheneList(AudioFileType, status=String(), limit=Int(), offset=Int())
    audio_files_by_group = GrapheneList(AudioFileType, group_id=Int())
    
    # TelegramGroup-Abfragen
    telegram_group = Field(TelegramGroupType, group_id=Int())
    telegram_groups = GrapheneList(TelegramGroupType)
    
    def resolve_audio_file(self, info, file_id):
        """Löst die audio_file-Abfrage auf."""
        try:
            return AudioFile.get_by_file_id(file_id)
        except AudioFile.DoesNotExist:
            return None
    
    def resolve_audio_files(self, info, status=None, limit=None, offset=None):
        """Löst die audio_files-Abfrage auf."""
        try:
            query = AudioFile.select()
            if status:
                query = query.where(AudioFile.status == status)
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            return list(query)
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von AudioFiles: {e}")
            return []
    
    def resolve_audio_files_by_group(self, info, group_id):
        """Löst die audio_files_by_group-Abfrage auf."""
        try:
            return list(AudioFile.select().where(AudioFile.group_id == group_id))
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von AudioFiles nach Gruppe: {e}")
            return []
    
    def resolve_telegram_group(self, info, group_id):
        """Löst die telegram_group-Abfrage auf."""
        try:
            return TelegramGroup.get_by_group_id(group_id)
        except TelegramGroup.DoesNotExist:
            return None
    
    def resolve_telegram_groups(self, info):
        """Löst die telegram_groups-Abfrage auf."""
        try:
            return list(TelegramGroup.select())
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von TelegramGroups: {e}")
            return []


# GraphQL-Schema erstellen
schema = graphene.Schema(query=Query)


class DatabaseAPI:
    """Verwaltet die Datenbank-API."""
    
    def __init__(self, app: Flask = None):
        """
        Initialisiert die Datenbank-API.
        
        Args:
            app: Flask-Anwendung
        """
        self.app = app or Flask(__name__)
        self.blueprint = Blueprint('database_api', __name__)
        self._setup_routes()
        self._setup_graphql()
        
        if app:
            self.init_app(app)
        
        logger.info("DatabaseAPI initialisiert")
    
    def init_app(self, app: Flask) -> None:
        """
        Initialisiert die API mit einer Flask-Anwendung.
        
        Args:
            app: Flask-Anwendung
        """
        app.register_blueprint(self.blueprint, url_prefix='/api/v1')
        logger.debug("DatabaseAPI mit Flask-Anwendung registriert")
    
    def _setup_routes(self) -> None:
        """Richtet die REST-API-Routen ein."""
        # AudioFile-Routen
        self.blueprint.add_url_rule('/audio-files', 
                                  view_func=self.get_audio_files, 
                                  methods=['GET'])
        self.blueprint.add_url_rule('/audio-files/<file_id>', 
                                  view_func=self.get_audio_file, 
                                  methods=['GET'])
        self.blueprint.add_url_rule('/audio-files', 
                                  view_func=self.create_audio_file, 
                                  methods=['POST'])
        self.blueprint.add_url_rule('/audio-files/<file_id>', 
                                  view_func=self.update_audio_file, 
                                  methods=['PUT'])
        self.blueprint.add_url_rule('/audio-files/<file_id>', 
                                  view_func=self.delete_audio_file, 
                                  methods=['DELETE'])
        
        # TelegramGroup-Routen
        self.blueprint.add_url_rule('/groups', 
                                  view_func=self.get_telegram_groups, 
                                  methods=['GET'])
        self.blueprint.add_url_rule('/groups/<int:group_id>', 
                                  view_func=self.get_telegram_group, 
                                  methods=['GET'])
        self.blueprint.add_url_rule('/groups', 
                                  view_func=self.create_telegram_group, 
                                  methods=['POST'])
        
        # Statistik-Routen
        self.blueprint.add_url_rule('/stats', 
                                  view_func=self.get_statistics, 
                                  methods=['GET'])
        
        # Validierungs-Routen
        self.blueprint.add_url_rule('/validate', 
                                  view_func=self.validate_database, 
                                  methods=['POST'])
    
    def _setup_graphql(self) -> None:
        """Richtet das GraphQL-Interface ein."""
        self.app.add_url_rule('/graphql', 
                             view_func=GraphQLView.as_view('graphql', 
                                                          schema=schema, 
                                                          graphiql=True))
    
    def _require_api_key(self, f):
        """Dekorator für API-Key-Authentifizierung."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In einer echten Implementierung würden wir hier
            # eine echte Authentifizierung durchführen
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API-Key erforderlich'}), 401
            
            # Für dieses Beispiel akzeptieren wir jeden API-Key
            # In einer echten Implementierung würden wir ihn validieren
            return f(*args, **kwargs)
        return decorated_function
    
    def _validate_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validiert Daten gegen erforderliche Felder.
        
        Args:
            data: Zu validierende Daten
            required_fields: Liste erforderlicher Felder
            
        Returns:
            True, wenn die Validierung erfolgreich war
        """
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        return True
    
    # AudioFile-Endpunkte
    def get_audio_files(self) -> Any:
        """Gibt eine Liste von AudioFiles zurück."""
        try:
            # Parameter aus der Anfrage extrahieren
            status = request.args.get('status')
            limit = request.args.get('limit', type=int)
            offset = request.args.get('offset', type=int, default=0)
            
            # Datenbankabfrage durchführen
            query = AudioFile.select()
            if status:
                query = query.where(AudioFile.status == status)
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            audio_files = []
            for audio in query:
                audio_files.append({
                    'id': audio.id,
                    'file_id': audio.file_id,
                    'file_name': audio.file_name,
                    'file_size': audio.file_size,
                    'duration': audio.duration,
                    'title': audio.title,
                    'performer': audio.performer,
                    'group_id': audio.group_id,
                    'downloaded_at': audio.downloaded_at.isoformat() if audio.downloaded_at else None,
                    'status': audio.status,
                    'error_message': audio.error_message,
                    'download_attempts': audio.download_attempts
                })
            
            return jsonify({
                'audio_files': audio_files,
                'count': len(audio_files)
            })
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von AudioFiles: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    def get_audio_file(self, file_id: str) -> Any:
        """Gibt ein einzelnes AudioFile zurück."""
        try:
            audio = AudioFile.get_by_file_id(file_id)
            if not audio:
                return jsonify({'error': 'AudioFile nicht gefunden'}), 404
            
            return jsonify({
                'id': audio.id,
                'file_id': audio.file_id,
                'file_name': audio.file_name,
                'file_size': audio.file_size,
                'duration': audio.duration,
                'title': audio.title,
                'performer': audio.performer,
                'group_id': audio.group_id,
                'downloaded_at': audio.downloaded_at.isoformat() if audio.downloaded_at else None,
                'status': audio.status,
                'error_message': audio.error_message,
                'download_attempts': audio.download_attempts
            })
            
        except AudioFile.DoesNotExist:
            return jsonify({'error': 'AudioFile nicht gefunden'}), 404
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von AudioFile {file_id}: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    def create_audio_file(self) -> Any:
        """Erstellt ein neues AudioFile."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Keine JSON-Daten bereitgestellt'}), 400
            
            # Validiere erforderliche Felder
            required_fields = ['file_id', 'file_name', 'group_id', 'status']
            if not self._validate_data(data, required_fields):
                return jsonify({'error': 'Erforderliche Felder fehlen'}), 400
            
            # Erstelle neues AudioFile
            audio = AudioFile.create(
                file_id=data['file_id'],
                file_name=data['file_name'],
                file_size=data.get('file_size'),
                duration=data.get('duration'),
                title=data.get('title'),
                performer=data.get('performer'),
                group_id=data['group_id'],
                downloaded_at=data.get('downloaded_at'),
                status=data['status'],
                error_message=data.get('error_message'),
                download_attempts=data.get('download_attempts', 0)
            )
            
            return jsonify({
                'id': audio.id,
                'message': 'AudioFile erfolgreich erstellt'
            }), 201
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen von AudioFile: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    def update_audio_file(self, file_id: str) -> Any:
        """Aktualisiert ein vorhandenes AudioFile."""
        try:
            audio = AudioFile.get_by_file_id(file_id)
            if not audio:
                return jsonify({'error': 'AudioFile nicht gefunden'}), 404
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Keine JSON-Daten bereitgestellt'}), 400
            
            # Aktualisiere Felder
            updatable_fields = [
                'file_name', 'file_size', 'duration', 'title', 
                'performer', 'group_id', 'downloaded_at', 'status',
                'error_message', 'download_attempts'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(audio, field, data[field])
            
            audio.save()
            
            return jsonify({
                'id': audio.id,
                'message': 'AudioFile erfolgreich aktualisiert'
            })
            
        except AudioFile.DoesNotExist:
            return jsonify({'error': 'AudioFile nicht gefunden'}), 404
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren von AudioFile {file_id}: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    def delete_audio_file(self, file_id: str) -> Any:
        """Löscht ein AudioFile."""
        try:
            audio = AudioFile.get_by_file_id(file_id)
            if not audio:
                return jsonify({'error': 'AudioFile nicht gefunden'}), 404
            
            audio.delete_instance()
            
            return jsonify({
                'message': 'AudioFile erfolgreich gelöscht'
            })
            
        except AudioFile.DoesNotExist:
            return jsonify({'error': 'AudioFile nicht gefunden'}), 404
        except Exception as e:
            logger.error(f"Fehler beim Löschen von AudioFile {file_id}: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    # TelegramGroup-Endpunkte
    def get_telegram_groups(self) -> Any:
        """Gibt eine Liste von TelegramGroups zurück."""
        try:
            groups = []
            for group in TelegramGroup.select():
                groups.append({
                    'id': group.id,
                    'group_id': group.group_id,
                    'title': group.title,
                    'username': group.username
                })
            
            return jsonify({
                'telegram_groups': groups,
                'count': len(groups)
            })
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von TelegramGroups: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    def get_telegram_group(self, group_id: int) -> Any:
        """Gibt eine einzelne TelegramGroup zurück."""
        try:
            group = TelegramGroup.get_by_group_id(group_id)
            if not group:
                return jsonify({'error': 'TelegramGroup nicht gefunden'}), 404
            
            return jsonify({
                'id': group.id,
                'group_id': group.group_id,
                'title': group.title,
                'username': group.username
            })
            
        except TelegramGroup.DoesNotExist:
            return jsonify({'error': 'TelegramGroup nicht gefunden'}), 404
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von TelegramGroup {group_id}: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    def create_telegram_group(self) -> Any:
        """Erstellt eine neue TelegramGroup."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Keine JSON-Daten bereitgestellt'}), 400
            
            # Validiere erforderliche Felder
            required_fields = ['group_id', 'title']
            if not self._validate_data(data, required_fields):
                return jsonify({'error': 'Erforderliche Felder fehlen'}), 400
            
            # Erstelle neue TelegramGroup
            group = TelegramGroup.create(
                group_id=data['group_id'],
                title=data['title'],
                username=data.get('username')
            )
            
            return jsonify({
                'id': group.id,
                'message': 'TelegramGroup erfolgreich erstellt'
            }), 201
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen von TelegramGroup: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    # Statistik-Endpunkte
    def get_statistics(self) -> Any:
        """Gibt Datenbankstatistiken zurück."""
        try:
            # Hole Gesamtzahlen
            total_files = AudioFile.select().count()
            total_groups = TelegramGroup.select().count()
            
            # Hole Status-Verteilung
            status_distribution = {}
            for status in AudioFile.select(AudioFile.status).distinct():
                count = AudioFile.select().where(AudioFile.status == status.status).count()
                status_distribution[status.status] = count
            
            # Hole Gruppenstatistiken
            group_stats = []
            for group in TelegramGroup.select():
                file_count = AudioFile.select().where(AudioFile.group_id == group.id).count()
                group_stats.append({
                    'group_id': group.group_id,
                    'title': group.title,
                    'file_count': file_count
                })
            
            return jsonify({
                'total_files': total_files,
                'total_groups': total_groups,
                'status_distribution': status_distribution,
                'group_statistics': group_stats
            })
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Statistiken: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500
    
    # Validierungs-Endpunkte
    def validate_database(self) -> Any:
        """Führt eine Datenbankvalidierung durch."""
        try:
            validator = get_database_validator()
            validation_results = validator.run_full_validation()
            
            return jsonify(validation_results)
            
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankvalidierung: {e}")
            return jsonify({'error': 'Interner Serverfehler'}), 500


# Globale Instanz der API
_api: Optional[DatabaseAPI] = None


def get_database_api(app: Flask = None) -> DatabaseAPI:
    """
    Gibt die globale Instanz der DatabaseAPI zurück.
    
    Args:
        app: Flask-Anwendung (optional)
        
    Returns:
        DatabaseAPI-Instanz
    """
    global _api
    if _api is None:
        _api = DatabaseAPI(app)
    return _api


def create_database_api(app: Flask) -> DatabaseAPI:
    """
    Erstellt und konfiguriert die Datenbank-API.
    
    Args:
        app: Flask-Anwendung
        
    Returns:
        DatabaseAPI-Instanz
    """
    try:
        api = DatabaseAPI(app)
        return api
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Datenbank-API: {e}")
        raise


def run_database_api_server(host: str = '127.0.0.1', port: int = 5000, 
                           debug: bool = False) -> None:
    """
    Startet den Datenbank-API-Server.
    
    Args:
        host: Host-Adresse
        port: Port-Nummer
        debug: Debug-Modus
    """
    try:
        app = Flask(__name__)
        api = get_database_api(app)
        
        # Einfache Status-Route
        @app.route('/health')
        def health_check():
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
        
        logger.info(f"Starte Datenbank-API-Server auf {host}:{port}")
        # Debug-Modus wird nur aktiviert, wenn explizit gewünscht und in einer Entwicklungsumgebung
        use_debug = debug and os.environ.get('FLASK_ENV') == 'development'
        
        # Sicherstellen, dass der Debug-Modus in Produktion immer aus ist
        if os.environ.get('FLASK_ENV') == 'production':
            use_debug = False
            
        app.run(host=host, port=port, debug=use_debug)
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Datenbank-API-Servers: {e}")
        raise


if __name__ == "__main__":
    # Wenn das Skript direkt ausgeführt wird, starte den API-Server
    # Debug-Modus ist standardmäßig deaktiviert
    run_database_api_server(debug=False)