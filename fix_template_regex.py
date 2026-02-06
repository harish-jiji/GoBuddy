import re
import os

file_path = r"c:\project\TOURISM\templates\admin\package_form.html"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find == without spaces on either side, inside {% ... %} tags ideally, 
    # but strictly catching non-space==non-space is safe enough for this file.
    # Note: Javascript might use ==, so we must be careful not to break JS.
    # The error is in Django tags: {% if x==y %}
    
    def replacer(match):
        return f"{match.group(1)} == {match.group(2)}"

    # Only target strings inside {% %} blocks
    # This is harder with regex.
    # Let's target specific known patterns or just the exact bad lines again but with looser matching.
    
    # Pattern: form.*.value==
    new_content = re.sub(r'(form\.[a-zA-Z0-9_]+\.value)==', r'\1 == ', content)
    
    # Pattern: ==choice.0
    new_content = re.sub(r'==choice\.0', r' == choice.0', new_content)
    
    # Pattern: ==value
    new_content = re.sub(r'==value', r' == value', new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated package_form.html with regex.")
    else:
        print("No changes needed (regex found nothing).")

except Exception as e:
    print(f"Error: {e}")
