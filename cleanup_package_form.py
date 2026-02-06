
import re

path = r"c:\project\TOURISM\templates\admin\package_form.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove <template id="dayTemplate">...</template>
# We'll use regex or simple string replacement if we can identify the block.
# It starts at line 194 and ends at 295.
content = re.sub(r'<template id="dayTemplate">.*?</template>', '', content, flags=re.DOTALL)

# 2. Update init() and updateItineraryDays() to remove accommodation and food_spot
# We look for lines like `accommodation: '',` and `food_spot: '',` inside the script and remove them.
# There are two occurrences (one in updateItineraryDays, one in init).

content = re.sub(r"\s+accommodation: '',", "", content)
content = re.sub(r"\s+food_spot: '',", "", content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Cleaned up template and JS initialization.")
