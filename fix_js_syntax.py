
path = r"c:\project\TOURISM\templates\admin\package_form.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the Python f-string syntax in JS
# Broken: ${subTypeOptions.map(opt => f'<option value="{opt["value"]}" {"selected" if currentSubType == opt["value"] else ""}>{opt["label"]}</option>').join('')}
# Correct: ${subTypeOptions.map(opt => `<option value="${opt.value}" ${currentSubType == opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}

# There are two occurrences in the file (one in the generated HTML string, and one in my view_file output but let's just fix the file content).
# Actually, looking at the view_file, it seems I pasted the comments and the "Correction" text into the JS file too!
# I need to remove that garbage.

# Helper to remove garbage lines
garbage_lines = [
    "// Wait, f-string in python script, I need to escape curly braces or use .format or simple string concat.",
    "// Correction: since I am writing JS code inside a Python string, I must be careful.",
    "// The JS code should be exactly as it is."
]

for gag in garbage_lines:
    content = content.replace(gag, "")

# Fix the f-string line
# It's tricky to match exactly because of quoting.
# Let's match the start `subTypeOptions.map(opt => f'`
import re

# We will use regex to find the broken map call.
# Pattern matches: subTypeOptions.map(opt => f'<option ... .join('')}
# We'll replace it with the correct JS.

broken_pattern = r'\$\{subTypeOptions\.map\(opt => f\'<option.*?\)\.join\(\'\'\)\}'
correct_js = "${subTypeOptions.map(opt => `<option value=\"${opt.value}\" ${currentSubType == opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}"

# Since regex with complex string can be hard, let's try simple string replace first if we can construct the exact broken string.
# Based on the view_file:
broken_string = """${subTypeOptions.map(opt => f'<option value="{opt["value"]}" {"selected" if currentSubType == opt["value"] else ""}>{opt["label"]}</option>').join('')}"""

if broken_string in content:
    content = content.replace(broken_string, correct_js)
    print("Fixed f-string syntax.")
else:
    print("Could not find exact broken string. Trying regex.")
    # The view show `opt["value"]` etc.
    # Regex:
    content_sub = re.sub(r'\$\{subTypeOptions\.map\(opt => f\'<option.*join\(\'\'\)\}', correct_js, content)
    if content_sub != content:
        content = content_sub
        print("Fixed f-string syntax with regex.")
    else:
        print("Failed to fix syntax.")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
