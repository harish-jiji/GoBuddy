import re

file_path = r"c:\project\TOURISM\templates\admin\package_form.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
for i, line in enumerate(lines):
    # Find tags
    tags = re.findall(r'{% (if|for|block|with|while) .*? %}|{% (endif|endfor|endblock|endwith|endwhile) %}', line)
    
    # Simple regex finding 'if' 'for' 'block' or 'end...'
    # Handle split tags roughly
    
    # Refined regex for exact tags
    open_tags = re.findall(r'{%\s*(if|for|block|with)\s+.*?%}', line)
    close_tags = re.findall(r'{%\s*(endif|endfor|endblock|endwith)\s*%}', line)
    
    # Manual scan to handle same-line open/close
    # This is rough, but might catch the obvious mismatch
    
    # Better approach: tokenize file by '{%' and '%}'
    pass

# Tokenizer approach
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

tokens = re.split(r'({%|%})', content)
current_line = 1
tag_stack = []

is_tag = False
for token in tokens:
    current_line += token.count('\n')
    if token == '{%':
        is_tag = True
        continue
    if token == '%}':
        is_tag = False
        continue
    
    if is_tag:
        token = token.strip()
        parts = token.split()
        if not parts: continue
        tag_name = parts[0]
        
        if tag_name in ['if', 'for', 'block', 'with']:
            tag_stack.append((tag_name, current_line))
        elif tag_name in ['endif', 'endfor', 'endblock', 'endwith']:
            if not tag_stack:
                print(f"Error: Unexpected {tag_name} at line {current_line}")
                continue
            last_tag, last_line = tag_stack.pop()
            expected_close = 'end' + last_tag
            if tag_name != expected_close:
                print(f"Error: Mismatch at line {current_line}. Found {tag_name}, expected {expected_close} for {last_tag} opened at line {last_line}")

if tag_stack:
    print("Unclosed tags:")
    for tag, line in tag_stack:
        print(f"{tag} at line {line}")
else:
    print("No unbalanced tags found.")
