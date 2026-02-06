
path = r"c:\project\TOURISM\templates\admin\package_form.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# I want to remove the "Night Stay" and "Dining" section in the renderItinerary function.
# It looks like:
# <!-- END OF DAY -->
# <div ...>
#    ... Night Stay ...
#    ... Dining ...
# </div>

# We can use a regex to match it.
import re

pattern = r'<!-- END OF DAY -->\s+<div class="mt-8 pt-6 border-t border-white/10 grid grid-cols-1 md:grid-cols-2 gap-6">.*?</div>\s+</div>'
# Note: The closing </div> matches the inner div. I need to be careful with nested divs.
# The block ends before the closing </div> of the day-card (glass p-5 ...)

# Let's target the inner content specifically to be safe.
# It contains "Night Stay" and "Dining".
start_str = '<!-- END OF DAY -->'
if start_str in content:
    # Find the start
    start_idx = content.find(start_str)
    # Find the end of this block. It is a div with class "mt-8...".
    # It closes with </div>.
    # It contains "Night Stay" and "Dining".
    
    # Let's search for the closing div of this specific block.
    # We can search for the next `</div>` after "Dining".
    
    dining_idx = content.find('Dining', start_idx)
    if dining_idx != -1:
         # Find the closing div for the input container of Dining
         end_input_div = content.find('</div>', dining_idx)
         # Find the closing div for the main grid container
         end_grid_div = content.find('</div>', end_input_div + 6)
         
         # Verification:
         # <div class="mt-8 ..."> (Parent)
         #   <div> (Col 1) ... </div>
         #   <div> (Col 2) ... </div>
         # </div>
         
         # So we need to match 3 closing divs after "Night Stay".
         
         # Let's try to just remove the lines.
         lines = content.split('\n')
         new_lines = []
         skip = False
         for line in lines:
             if '<!-- END OF DAY -->' in line:
                 skip = True
             
             if skip:
                 # We want to skip until we think we are done.
                 # This block is inside the backticks `...` of dayHtml.
                 # It ends before `</div>` (closing day-card).
                 # The validation: simpler to just identifying the string range in python string ops.
                 pass
             else:
                 new_lines.append(line)
         
         # Rethink: string replace is safer if I have the exact content.
         
         target_block = """                    <!-- END OF DAY -->
                    <div class="mt-8 pt-6 border-t border-white/10 grid grid-cols-1 md:grid-cols-2 gap-6">
                         <div>
                            <label class="text-[10px] text-purple-400 uppercase font-bold mb-1 block">Night Stay</label>
                            <input type="text" value="${day.accommodation || ''}" 
                                class="w-full bg-black/20 border border-white/10 rounded px-3 py-2 text-white outline-none focus:border-purple-500 transition"
                                placeholder="Hotel/Stay..."
                                onchange="updateDayField(${index}, 'accommodation', this.value)">
                        </div>
                        <div>
                            <label class="text-[10px] text-orange-400 uppercase font-bold mb-1 block">Dining</label>
                            <input type="text" value="${day.food_spot || ''}" 
                                class="w-full bg-black/20 border border-white/10 rounded px-3 py-2 text-white outline-none focus:border-orange-500 transition"
                                placeholder="Dinner spot..."
                                onchange="updateDayField(${index}, 'food_spot', this.value)">
                        </div>
                    </div>"""
         
         if target_block in content:
             content = content.replace(target_block, "")
             with open(path, 'w', encoding='utf-8') as f:
                 f.write(content)
             print("Successfully removed END OF DAY block.")
         else:
             # Maybe whitespace mismatch. normalize spaces.
             print("Could not find exact block. Retrying with regex.")
             regex = r'<!-- END OF DAY -->\s*<div.*?>\s*<div>\s*<label.*?Night Stay</label>.*?</div>\s*<div>\s*<label.*?Dining</label>.*?</div>\s*</div>'
             
             # The regex needs to handle multiline.
             content_sub = re.sub(regex, '', content, flags=re.DOTALL)
             if content_sub != content:
                 with open(path, 'w', encoding='utf-8') as f:
                     f.write(content_sub)
                 print("Successfully removed END OF DAY block with regex.")
             else:
                 print("Failed to remove block.")

else:
    print("Start marker not found.")

