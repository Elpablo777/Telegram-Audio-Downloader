import re

def fix_whitespace_issues(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove blank lines with only whitespace
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
    
    # Ensure there's a newline at the end of the file
    if not content.endswith('\n'):
        content += '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_whitespace_issues('src/telegram_audio_downloader/cli.py')
    print("Whitespace issues fixed successfully!")