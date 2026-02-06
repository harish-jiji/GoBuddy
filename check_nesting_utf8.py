import re

def check_nesting(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    stack = []
    start_tag_re = re.compile(r'{%\s*(if|for|block|with)\s+.*%}')
    end_tag_re = re.compile(r'{%\s*(endif|endfor|endblock|endwith)\s*%}')

    output = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Check for start tags
        start_matches = start_tag_re.finditer(line)
        for match in start_matches:
            tag_type = match.group(1)
            stack.append((tag_type, line_num))

        # Check for end tags
        end_matches = end_tag_re.finditer(line)
        for match in end_matches:
            tag_type = match.group(1) # endif, endfor, etc.
            expected_start = tag_type[3:] # remove 'end'
            
            if not stack:
                output.append(f"ERROR: Line {line_num}: Found {tag_type} but no open block.")
                continue

            last_open, last_line = stack.pop()
            if last_open != expected_start:
                 output.append(f"ERROR: Line {line_num}: Found {tag_type} but expected end of {last_open} (opened at line {last_line})")

    if stack:
        output.append("\nERROR: Unclosed blocks at end of file:")
        for tag, line in stack:
            output.append(f"  {tag} opened at line {line}")
    
    with open('nesting_result_utf8.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

file_path = r"c:\project\TOURISM\templates\admin\package_form.html"
check_nesting(file_path)
