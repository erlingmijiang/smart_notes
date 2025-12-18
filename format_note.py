import re

def format_note(text):
    """
    格式化输出文本，调节大小标题逻辑，并插入空行调节排版
    """
    # 将文本按行分割
    lines = text.split('\n')
    formatted_lines = []
    
    # 第一步：收集所有标题信息，用于判断是否需要添加【笔记主题】
    headers = []
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            header_match = re.match(r'^(#+)', stripped_line)
            if header_match:
                header_level = len(header_match.group(1))
                headers.append((i, header_level, stripped_line))
    
    # 判断是否需要添加【笔记主题】
    first_header_level = None
    level_1_count = 0
    first_level_1_index = -1
    
    for i, level, content in headers:
        if first_header_level is None:
            first_header_level = level
        if level == 1:
            level_1_count += 1
            if first_level_1_index == -1:
                first_level_1_index = i
    
    need_add_theme = (first_header_level == 1 and level_1_count == 1)
    
    # 第二步：重新处理文本
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()
        
        # 处理标题行
        if stripped_line.startswith('#'):
            # 在标题前添加空行（如果不是第一行且前一行不是空行）
            if formatted_lines and formatted_lines[-1].strip() != '':
                formatted_lines.append('')
            
            # 减少标题级别（#数量减一，但至少保留一个#）
            header_match = re.match(r'^(#+)', stripped_line)
            if header_match:
                header_level = len(header_match.group(1))
                new_level = max(1, header_level - 1)  # 至少保留1级标题
                new_header = '#' * new_level
                new_line = stripped_line.replace(header_match.group(1), new_header, 1)
                
                # 如果是第一个一级标题且需要添加主题标记
                if need_add_theme and i == first_level_1_index and new_level == 1:
                    new_line = "# 【笔记主题】" + new_line[1:].strip()
                
                formatted_lines.append(new_line)
            else:
                formatted_lines.append(stripped_line)
            
            # 在标题后添加空行
            formatted_lines.append('')
            
        # 处理有序列表（以数字+.+空格开头）
        elif re.match(r'^\s*\d+\.\s+', stripped_line):
            # 判断前一行是否也是列表项
            prev_is_ordered_list = False
            prev_is_unordered_list = False
            if formatted_lines:
                prev_line = formatted_lines[-1].strip()
                if re.match(r'^\s*\d+\.\s+', prev_line):
                    prev_is_ordered_list = True
                elif re.match(r'^\s*[\*\-]\s+', prev_line):
                    prev_is_unordered_list = True
            
            # 默认情况下，连续的有序列表项不需要空行
            need_space = False
            if prev_is_ordered_list:
                # 提取前一行和当前行的数字
                prev_match = re.match(r'^\s*(\d+)\.', formatted_lines[-1].strip())
                curr_match = re.match(r'^\s*(\d+)\.', stripped_line)
                if prev_match and curr_match:
                    prev_num = int(prev_match.group(1))
                    curr_num = int(curr_match.group(1))
                    # 如果不是连续的数字，或者前一行包含冒号（主题标题），则需要空行
                    if curr_num != prev_num + 1 or '：' in formatted_lines[-1]:
                        need_space = True
            elif prev_is_unordered_list:
                # 前一行是无序列表，需要根据缩进级别判断是否需要空行
                prev_line = formatted_lines[-1]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                curr_indent = len(line) - len(line.lstrip())
                
                # 如果前一行缩进较深（嵌套列表），转换为有序列表时不需要空行
                # 如果前一行缩进较浅，且当前有序列表项包含冒号（主题标题），则需要空行
                if prev_indent >= 6:  # 较深缩进
                    need_space = False
                elif '：' in stripped_line:  # 主题标题
                    need_space = True
                else:
                    need_space = False
            else:
                # 如果前一行不是列表，则需要空行
                need_space = True
            
            # 根据需要添加空行
            if need_space and formatted_lines:
                prev_line = formatted_lines[-1].strip()
                if prev_line.startswith('#'):
                    formatted_lines.append('')
                elif prev_line != '' and not prev_line.startswith('>') and not re.match(r'^\s*\d+\.\s+', prev_line):
                    # 如果前一行是普通正文（不是列表项），需要空行
                    formatted_lines.append('')
            
            formatted_lines.append(line)
        
        # 处理无序列表（以*或-+空格开头）
        elif re.match(r'^\s*[\*\-]\s+', stripped_line):
            # 判断前一行是否也是列表项（包括有序和无序）
            prev_is_ordered_list = False
            prev_is_unordered_list = False
            if formatted_lines:
                prev_line = formatted_lines[-1].strip()
                if re.match(r'^\s*\d+\.\s+', prev_line):
                    prev_is_ordered_list = True
                elif re.match(r'^\s*[\*\-]\s+', prev_line):
                    prev_is_unordered_list = True
            
            # 从有序列表转换到无序列表时的处理
            # 无序列表之间紧密排版，不插入空行
            # 如果前一行不是列表项，需要空行分隔
            need_space = False
            if prev_is_ordered_list:
                # 检查缩进级别：如果当前无序列表缩进较深，说明是有序列表的子项，不需要空行
                # 如果当前无序列表没有缩进或缩进较浅，说明是新的主题，需要空行
                prev_line = formatted_lines[-1]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                curr_indent = len(line) - len(line.lstrip())
                
                if curr_indent > prev_indent:
                    need_space = False  # 子项，不需要空行
                else:
                    need_space = True   # 新主题，需要空行
            elif not prev_is_unordered_list and formatted_lines:
                prev_line = formatted_lines[-1].strip()
                if prev_line.startswith('#'):
                    need_space = True
                elif prev_line != '' and not prev_line.startswith('>'):
                    # 如果前一行是普通正文，也需要空行
                    need_space = True
            
            # 根据需要添加空行
            if need_space and formatted_lines:
                formatted_lines.append('')
            
            formatted_lines.append(line)
            
        # 处理引用行（以>开头）
        elif stripped_line.startswith('>'):
            # 引用前添加空行（如果不是第一行且前一行不是空行且不是引用）
            if formatted_lines and formatted_lines[-1].strip() != '' and not formatted_lines[-1].strip().startswith('>'):
                formatted_lines.append('')
            
            formatted_lines.append(line)
            
        # 处理分隔线（---或***）
        elif stripped_line in ['---', '***', '----']:
            # 分隔线前添加空行（如果不是第一行且前一行不是空行）
            if formatted_lines and formatted_lines[-1].strip() != '':
                formatted_lines.append('')
            
            formatted_lines.append(line)
            
            # 分隔线后添加空行
            if i < len(lines) - 1:
                formatted_lines.append('')
        
        # 处理普通正文
        elif stripped_line != '':
            # 如果前一行是标题，已经添加过空行了
            # 如果前一行是正文且不是空行，添加空行
            if (formatted_lines and 
                formatted_lines[-1].strip() != '' and 
                not formatted_lines[-1].strip().startswith('#') and
                not formatted_lines[-1].strip().startswith('>') and
                not re.match(r'^\s*[\d\*\-\+]\s+', formatted_lines[-1].strip())):
                formatted_lines.append('')
            
            formatted_lines.append(line)
        
        # 处理空行
        else:
            # 保留原有的空行，但避免连续空行过多
            if not formatted_lines or formatted_lines[-1].strip() != '':
                formatted_lines.append(line)
        
        i += 1
    
    # 重新组合文本
    text = '\n'.join(formatted_lines)
    
    # 清理多余的连续空行（超过2个空行的情况）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text