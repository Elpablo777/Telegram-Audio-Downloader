#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Audio Downloader

A robust script to download all audio files from a Telegram group.

Requirements:
- Python 3.7+
- telethon
- python-dotenv
- tqdm

Configuration:
Create a .env file in the same directory with the following variables:
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_NAME=your_session_name
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import MessageMediaDocument, DocumentAttributeAudio
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Audio file extensions to look for
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.ogg', '.flac', '.wav'}

class AudioDownloader:
    def __init__(self):
        self.client = None
        self.downloaded_files = set()
        self.total_downloaded = 0
        self.errors = []

    async def initialize_client(self):
        """Initialize the Telegram client with credentials from .env"""
        api_id = os.getenv('API_ID')
        api_hash = os.getenv('API_HASH')
        session_name = os.getenv('SESSION_NAME', 'session')

        if not all([api_id, api_hash]):
            raise ValueError("API_ID and API_HASH must be set in .env file")

        self.client = TelegramClient(session_name, int(api_id), api_hash)
        await self.client.start()

    def get_audio_info(self, document) -> Optional[dict]:
        """Extract audio file information from document"""
        if not hasattr(document, 'attributes'):
            return None

        for attr in document.attributes:
            if isinstance(attr, DocumentAttributeAudio):
                file_ext = Path(document.mime_type).suffix.lower()
                if not file_ext:
                    file_ext = '.mp3'  # Default extension if none found
                
                return {
                    'id': document.id,
                    'access_hash': document.access_hash,
                    'file_reference': document.file_reference,
                    'size': document.size,
                    'mime_type': document.mime_type,
                    'ext': file_ext,
                    'title': getattr(attr, 'title', f'audio_{document.id}'),
                    'performer': getattr(attr, 'performer', 'Unknown Artist'),
                    'duration': getattr(attr, 'duration', 0)
                }
        return None

    async def download_audio_files(self, group_entity, download_dir: str):
        """Download all audio files from the specified group"""
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)

        # Get all existing files to avoid re-downloading
        existing_files = {f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))}
        
        # Get total number of messages for progress bar
        total_messages = await self.client.get_messages(group_entity, limit=0).total
        
        print(f"Found {total_messages} total messages in the group.")
        print("Starting to scan for audio files...")
        
        # Process messages with progress bar
        with tqdm(total=total_messages, desc="Processing messages", unit="msg") as pbar:
            async for message in self.client.iter_messages(group_entity):
                try:
                    if message.media and hasattr(message.media, 'document'):
                        audio_info = self.get_audio_info(message.media.document)
                        if audio_info:
                            # Create a safe filename
                            safe_title = "".join(c if c.isalnum() or c in ' ._-' else '_' for c in audio_info['title'])
                            filename = f"{safe_title}{audio_info['ext']}"
                            filepath = os.path.join(download_dir, filename)
                            
                            # Skip if file already exists
                            if filename in existing_files:
                                pbar.set_postfix_str(f"Skipped (exists): {filename}")
                                continue
                            
                            # Download the file with progress
                            try:
                                pbar.set_postfix_str(f"Downloading: {filename}")
                                
                                # Create a custom progress bar for the download
                                with tqdm(
                                    total=audio_info['size'],
                                    unit='B',
                                    unit_scale=True,
                                    unit_divisor=1024,
                                    desc=filename[:30],
                                    leave=False
                                ) as d_pbar:
                                    def callback(received_bytes, total):
                                        d_pbar.update(received_bytes - d_pbar.n)
                                    
                                    await self.client.download_media(
                                        message,
                                        file=filepath,
                                        progress_callback=callback
                                    )
                                
                                self.total_downloaded += 1
                                pbar.set_postfix_str(f"Downloaded: {filename}")
                                
                            except Exception as e:
                                self.errors.append(f"Error downloading {filename}: {str(e)}")
                                pbar.set_postfix_str(f"Error: {str(e)[:20]}...")
                                
                except FloodWaitError as fwe:
                    wait_time = fwe.seconds
                    print(f"\nRate limit hit. Waiting for {wait_time} seconds as requested by Telegram...")
                    await asyncio.sleep(wait_time)
                    continue
                except RPCError as rpce:
                    self.errors.append(f"RPC Error: {str(rpce)}")
                    continue
                except Exception as e:
                    self.errors.append(f"Unexpected error: {str(e)}")
                    continue
                finally:
                    pbar.update(1)

    async def run(self):
        """Main execution method"""
        print("=" * 50)
        print("  Telegram Audio Downloader")
        print("  This script will download all audio files from a Telegram group")
        print("=" * 50)
        print()
        
        # Get user input
        group_identifier = input("Enter the exact name or ID of the Telegram group: ").strip()
        download_dir = input("Enter the full path to the download directory: ").strip()
        
        try:
            # Initialize client
            print("\nInitializing Telegram client...")
            await self.initialize_client()
            
            # Resolve the group entity
            print("Finding the group...")
            try:
                group_entity = await self.client.get_entity(group_identifier)
            except ValueError:
                # Try searching if the input is a username
                group_entity = await self.client.get_entity(f"https://t.me/{group_identifier}")
            
            print(f"\nFound group: {group_entity.title}")
            
            # Start downloading
            print(f"Downloading audio files to: {download_dir}")
            await self.download_audio_files(group_entity, download_dir)
            
            # Print summary
            print("\n" + "=" * 50)
            print("Download complete!")
            print(f"Total audio files downloaded: {self.total_downloaded}")
            
            if self.errors:
                print("\nThe following errors occurred:")
                for error in self.errors[:10]:  # Show first 10 errors to avoid flooding
                    print(f"- {error}")
                if len(self.errors) > 10:
                    print(f"... and {len(self.errors) - 10} more errors")
            
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            if hasattr(e, '__cause__') and e.__cause__:
                print(f"Caused by: {str(e.__cause__)}")
        finally:
            if self.client and self.client.is_connected():
                await self.client.disconnect()


if __name__ == "__main__":
    downloader = AudioDownloader()
    asyncio.run(downloader.run())
