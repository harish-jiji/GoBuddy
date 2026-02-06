import os

file_path = r"c:\project\TOURISM\templates\admin\package_form.html"

replacements = [
    ('form.category.value==choice.0', 'form.category.value == choice.0'),
    ('form.target_audience.value==value', 'form.target_audience.value == value'),
    ('form.accommodation_type.value==value', 'form.accommodation_type.value == value'),
    ('form.transportation_mode.value==value', 'form.transportation_mode.value == value'),
    ('form.meals_plan.value==value', 'form.meals_plan.value == value'),
]

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated package_form.html")
    else:
        print("No changes needed or strings not found.")

except Exception as e:
    print(f"Error: {e}")
