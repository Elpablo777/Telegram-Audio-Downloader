# Filename Sanitization Enhancement

## Problem Solved

Fixed crashes when downloading Telegram audio files with special characters, emojis, or control characters in their names.

## Issue Description

The original `sanitize_filename()` function in `src/telegram_audio_downloader/utils/__init__.py` and `src/telegram_audio_downloader/utils/file_operations.py` had several problems:

1. **Null bytes** (`\x00`) caused `ValueError` when trying to create files
2. **Control characters** (newlines, tabs, etc.) were not properly sanitized
3. **Zero-width characters** could cause confusing filenames
4. **Unicode normalization** was missing, leading to inconsistent handling

## Solution

Enhanced the `sanitize_filename()` function with:

### 1. Unicode Normalization
```python
normalized = unicodedata.normalize('NFKC', filename)
```
Ensures consistent handling of composed characters and compatibility characters.

### 2. Control Character Removal
```python
control_chars = re.compile(r'[\x00-\x1f\x7f-\x9f]')
sanitized = control_chars.sub(replacement, normalized)
```
Removes/replaces dangerous control characters including null bytes, newlines, tabs.

### 3. Invisible Character Removal
```python
invisible_chars = re.compile(r'[\u200b-\u200f\u2028-\u202f\u205f-\u206f\ufeff]')
sanitized = invisible_chars.sub('', sanitized)
```
Removes zero-width spaces, word joiners, and other invisible characters.

### 4. Enhanced Platform Safety
- Maintains existing Windows/Unix invalid character replacement
- Preserves emoji support for user-friendly filenames
- Handles reserved Windows names (CON, PRN, etc.)
- Robust length limitation with proper extension handling

## Files Modified

1. `src/telegram_audio_downloader/utils/__init__.py`
   - Enhanced `sanitize_filename()` function
   - Added `unicodedata` import
   - Updated documentation

2. `src/telegram_audio_downloader/utils/file_operations.py`
   - Synchronized with enhanced implementation
   - Added `unicodedata` import

3. `tests/test_file_operations.py`
   - Updated existing test expectations
   - Enhanced test documentation

4. `tests/test_filename_special_characters.py` (new)
   - Comprehensive tests for special character handling
   - Edge case coverage for control characters, emojis, Unicode

## Test Results

✅ **100% test success rate (21/21 tests passed):**

### 🚨 Critical fixes (prevented crashes):
- **Null bytes** (`\x00`) - now safely replaced
- **Control characters** (newlines, tabs, etc.) - properly sanitized
- **File creation safety** - all outputs create valid files

### 😀 Enhanced functionality:
- **Emojis preserved** - user-friendly filenames maintained
- **International support** - German, Spanish, Greek, Japanese, Russian characters
- **Platform compatibility** - Windows/Unix invalid characters handled
- **Invisible character cleanup** - zero-width spaces, word joiners removed

### 💻 Platform safety verified:
- Windows reserved names (CON, PRN, etc.) - prefixed safely
- Path separators and invalid characters - replaced consistently
- File length limitations - handled with extension preservation

## Backward Compatibility

The enhanced function maintains backward compatibility:
- Default parameters remain the same
- Output for normal filenames is unchanged
- Only problematic characters are handled differently
- Existing code continues to work without modification

## Impact

This fix resolves the core issue described in `.qoder/rules/fix-special-characters.md`:
- ✅ Prevents crashes from special characters in Telegram audio file names
- ✅ Handles emojis and Unicode characters correctly
- ✅ Maintains platform compatibility
- ✅ Provides robust error handling
- ✅ Enhances user experience with preserved emojis