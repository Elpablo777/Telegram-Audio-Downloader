def fix_docstring_whitespace(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process lines to remove whitespace-only lines within docstrings
    fixed_lines = []
    in_docstring = False
    
    for line in lines:
        # Check if we're entering or leaving a docstring
        if '"""' in line and not in_docstring:
            in_docstring = True
            fixed_lines.append(line)
        elif '"""' in line and in_docstring:
            in_docstring = False
            fixed_lines.append(line)
        elif in_docstring and line.strip() == '':
            # Skip whitespace-only lines within docstrings
            continue
        else:
            fixed_lines.append(line)
    
    # Ensure file ends with a single newline
    content = ''.join(fixed_lines)
    if not content.endswith('\n'):
        content += '\n'
    elif content.endswith('\n\n'):
        content = content.rstrip() + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_docstring_whitespace('src/telegram_audio_downloader/cli.py')
    print("Docstring whitespace issues fixed successfully!")