import re
from string import Template

# Test the regular expression
pattern = r'\$(\w+)|\$\{(\w+)\}'
template_string = '$artist - $title - $counter'
matches = re.findall(pattern, template_string)

print('Pattern:', pattern)
print('Template string:', template_string)
print('Matches:', matches)

# Extrahiere die Platzhalter
placeholders = set()
for match in matches:
    # match is a tuple, one of the two elements is the placeholder
    # In each tuple, one of the elements is empty, the other contains the placeholder
    placeholder = match[0] if match[0] else match[1]
    placeholders.add(placeholder)
    
print('Extracted placeholders:', placeholders)

# Teste das Rendern
template = Template(template_string)
template_data = {
    "artist": "Test Artist",
    "title": "Test Title",
    "counter": "005"
}

try:
    result = template.substitute(template_data)
    print('Rendered result:', result)
except KeyError as e:
    print('KeyError:', e)
    result = template.safe_substitute(template_data)
    print('Safe substitute result:', result)