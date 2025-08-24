import re

pattern = r'\$(\w+)|\$\{(\w+)\}'
template_string = '$artist - $title - $counter'
matches = re.findall(pattern, template_string)

print('Pattern:', pattern)
print('Template string:', template_string)
print('Matches:', matches)