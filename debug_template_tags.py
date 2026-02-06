
import re

def find_unclosed_tags(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    stack = []
    
    # Regex for start and end tags
    # We care about: if, for, block (though block is usually top level), with
    # invalid block tag means we hit endblock but expected endif/endfor
    
    tag_pattern = re.compile(r'{%\s*(if|for|while|with|block|endIF|endFOR|endWHILE|endWITH|endBLOCK|endif|endfor|endwhile|endwith|endblock)\b')

    for i, line in enumerate(lines):
        line_num = i + 1
        pos = 0
        while True:
            match = tag_pattern.search(line, pos)
            if not match:
                break
            
            tag = match.group(1).lower()
            
            if tag:
                 print(f"Line {line_num}: {tag}")

            # Start tags
            if tag in ['if', 'for', 'while', 'with', 'block']:
                stack.append((tag, line_num))
            
            # End tags
            elif tag.startswith('end'):
                expected_start = tag[3:] # e.g. 'if' from 'endif'
                
                if not stack:
                    print(f"ERROR: Line {line_num}: Found {tag} but no open tags.")
                    return

                last_tag, last_line = stack[-1]
                
                if last_tag == expected_start:
                    stack.pop()
                    # print(f"Line {line_num}: Closed {last_tag} (opened at {last_line})")
                else:
                    print(f"ERROR: Line {line_num}: Found {tag} but expected end of {last_tag} (opened at {last_line})")
                    return

            pos = match.end()

    if stack:
        print("\nUnclosed tags remaining:")
        for tag, line in stack:
            print(f"- {tag} opened at line {line}")

if __name__ == "__main__":
    find_unclosed_tags(r"c:\project\TOURISM\templates\admin\trip_plan_edit.html")
