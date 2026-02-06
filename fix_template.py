path = r"c:\project\TOURISM\templates\admin\package_form.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the specific syntax error
content = content.replace('form.instance.target_audience=="single"', 'form.instance.target_audience == "single"')
content = content.replace('form.instance.target_audience=="couple"', 'form.instance.target_audience == "couple"')
content = content.replace('form.instance.target_audience=="family"', 'form.instance.target_audience == "family"')
content = content.replace('form.instance.target_audience=="friends"', 'form.instance.target_audience == "friends"')

# Fallback for generic case if exact match fails due to whitespace
content = content.replace('=="', ' == "')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated file successfully.")
