import pprint
import re
import os
import re
import subprocess
from datetime import datetime
import PyPDF2

# 月份映射表
MONTH_MAP = {
    'january': 'jan', 'february': 'feb', 'march': 'mar', 'april': 'apr',
    'june': 'jun', 'july': 'jul', 'august': 'aug',
    'september': 'sep', 'october': 'oct', 'november': 'nov', 'december': 'dec',
    'jan': 'jan', 'feb': 'feb', 'mar': 'mar', 'apr': 'apr',
    'may': 'may', 'jun': 'jun', 'jul': 'jul', 'aug': 'aug',
    'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dec': 'dec'
}

# 从 PDF 中提取日期信息
def extract_date_from_pdf(pdf_path):
    try:
        print('try:', pdf_path)
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            # only extract from the first page
            for page in reader.pages:
                if page.extract_text():
                    text = page.extract_text()
                    break

        # 将text中的所有连续空白字符替换为一个空格
        clean_text = re.sub(r'\s+', ' ', text)
        # print(clean_text)

        # match: VOL. 11, NO. 5, 1 MARCH 2024
        # VOL. 16, NO. 2, FEBRUARY 2017
        pattern0 = re.compile(
            r'VOL\.?\s*(?P<vol_num>\d+).?\s*NO\.?\s*(?P<art_num>\d+).?\s*(?P<day>\d+)?\s*'
            r'(?P<month>JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)'
            r'\s+(?P<year>\d{4})\b',
            flags=re.IGNORECASE
        )
        matches0 = [m.groupdict() for m in pattern0.finditer(text)]
        print("Pattern0:", [text[m.start(): m.end()] for m in pattern0.finditer(text)])
        if len(matches0) > 1:
            print("\033[91mWarning: Multiple matches!\033[0m")

        # match:  date of current version 16 September 2022
        match1 = re.search(r'date of current version[\s:]*(?P<day>[0-9]{1,2})[\s,]+(?P<month>[A-Za-z]+)[\s,]+(?P<year>[0-9]{4})', text, re.IGNORECASE)
        if match1:
            print("Pattern1:", text[match1.start(): match1.end()])

        # match:  date of current version July 16, 2021
        match2 = re.search(r'date of current version[\s:]*(?P<month>[A-Za-z]+)[\s,]+(?P<day>[0-9]{1,2})[\s,]+(?P<year>[0-9]{4})', text, re.IGNORECASE)
        if match2:
            print("Pattern2:", text[match2.start(): match2.end()])

        match = None

        if len(matches0) > 0:
            match = matches0[0]
        elif match1:
            match = match1.groupdict()
        elif match2:
            match = match2.groupdict()


        if match:
            month = MONTH_MAP[match['month'].lower()]
            year = match['year']
            return {'year': year, 'month': month}
    except Exception as e:
        print(f"\033[91mWarning: Error processing {pdf_path}: {e}\033[0m")
    return None


# 使用 Everything 搜索 PDF 文件路径
def search_and_extract_date_from_pdf(title, es_cmd_exe_path, auto_run_all=False):
    query = [word for word in title.split(' ') if len(word) > 3]
    print(f"------------Search results for \"{' '.join(query)}\":")
    if es_cmd_exe_path is None:
        cmd_input = ['es']
    else:
        cmd_input = [es_cmd_exe_path]
    cmd_input.extend(query)
    cmd_input.append('ext:pdf')
    result = subprocess.run(cmd_input, stdout=subprocess.PIPE, text=True)
    pdfs = result.stdout.strip().split('\n')
    # import pprint
    # pprint.pprint(pdfs)
    pdfs = [pdf for pdf in pdfs if pdf.strip()]

    new_ope = None
    while True:
        try:
            if auto_run_all:
                if not pdfs:
                    return None, new_ope
                res = extract_date_from_pdf(pdfs[0])
                if res is None:
                    print("Extract failed!")
                    return None, new_ope
                else:
                    return res, new_ope

            if not pdfs:
                print(f"No PDF found for title: {title}")
                user_input = input("-----------------Input new path / month and year like '2000 jun' / 'S' to skip / 'SS' to skip all / 'DD' to auto run all:").strip()
            else:
                for i, pdf in enumerate(pdfs):
                    print(f"{i}: {pdf}")
                user_input = input("-----------------press Enter for first result / input index to select a file / a new path / month and year like '2000 jun' / 'S' to skip / 'SS' to skip all / 'DD' to auto run all: ").strip()
            if user_input.lower() == 's':
                return None, new_ope
            elif user_input.lower() == 'ss':
                new_ope = 'ss'
                return None, new_ope
            elif user_input == "" or user_input.lower() == 'dd':
                res = extract_date_from_pdf(pdfs[0])
                if user_input.lower() == 'dd':
                    new_ope = 'dd'
                    return res, new_ope
                if res is None:
                    print("Extract failed!")
                    continue
                else:
                    return res, new_ope

            elif user_input.isdigit() and int(user_input) < len(pdfs):
                res = extract_date_from_pdf(pdfs[int(user_input)])
                if res is None:
                    print("Extract failed!")
                    continue
                else:
                    return res, new_ope

            elif os.path.exists(user_input):
                res = extract_date_from_pdf(user_input)
                if res is None:
                    print("Extract failed!")
                    continue
                else:
                    return res, new_ope

            else:
                month_and_year = user_input.split(' ')
                if month_and_year.__len__() == 2:
                    year, month = month_and_year[0], month_and_year[1]
                    if year.isdigit() and month in MONTH_MAP:
                        print(f"Month: {MONTH_MAP[month]}, Year: {year}")
                        return {'year': year, 'month': month}, new_ope
                print("Input illegal!")
                continue
        except Exception as e:
            print(f"\033[91mWarning: Error processing : {e}\033[0m")


# 主程序
def update_bib_year_and_month(entries, es_cmd_path):
    # entries : {'alice2000':{}, }
    skip_all = False
    auto_run_all = False
    for entry_name in entries:
        entry = entries[entry_name]
        if not skip_all:
            # 替换非字母字符为一个空格
            cleaned_title = re.sub(r'[^a-zA-Z]+', ' ', entry['title']).strip().lower()
            date_info, new_ope = search_and_extract_date_from_pdf(cleaned_title, es_cmd_path, auto_run_all=auto_run_all)
            if date_info:
                date_info['year'] = f'{{{date_info['year']}}}'
            print('get date:', date_info)
            if date_info:
                entry.update(date_info)
            if new_ope == 'dd':
                auto_run_all = True
            elif new_ope == 'ss':
                skip_all = True
    return entries


def extract_braced(text, start_index):
    """
    从 text 中，从 start_index 开始（要求该位置为 '{'）提取出匹配的最外层括号内容，
    返回 (braced_string, end_index)；braced_string 包括最外层花括号。
    """
    count = 0
    i = start_index
    while i < len(text):
        if text[i] == '{':
            count += 1
        elif text[i] == '}':
            count -= 1
            if count == 0:
                return text[start_index:i+1], i
        i += 1
    return None, start_index

def normalize_string(s):
    """
    将字符串 s 内的所有花括号去掉，空白标准化并转为小写，用于宽松匹配。
    """
    no_braces = re.sub(r'[{}]', '', s)
    normalized = ' '.join(no_braces.split()).lower()
    return normalized

def parse_ieee_mapping(ieee_path):
    """
    从IEEEfull.bib中解析出映射：
      key   : 规范化后的期刊全名（去除所有花括号、空白标准化、小写）
      value : 对应的缩写（例如IEEE_J_WCOM）
    假设IEEEfull.bib中的条目形如：
      @STRING{IEEE_J_WCOM = "{IEEE} Transactions on Wireless Communications"}
    """
    mapping = {}
    with open(ieee_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # 用正则查找@STRING{ ... =
    pattern = re.compile(r'@STRING\s*\{\s*([^=\s]+)\s*=\s*"([^"]+)"\s*}', flags=re.IGNORECASE)
    pos = 0
    while True:
        m = pattern.search(content, pos)
        if not m:
            break
        string_entry = m.group(1)
        i = m.end()
        full_name = m.group(2)
        normalized_full = normalize_string(full_name)
        mapping[normalized_full] = string_entry
        pos = i + 1

    return mapping


def remove_outer_braces(s):
    # 匹配字符串最外层的成对花括号
    pattern = r'^\{\s*(.*?)\s*\}$'
    while True:
        match = re.match(pattern, s)
        if match:
            s = match.group(1)  # 提取内部内容
        else:
            break
    return s

def process_title(title):
    """
    修改 entry 中 title 字段：
    找到 "title=" 后第一个 '{' 到匹配的最外层 '}'，
    如果内部内容未被双层括号包裹，则用双层括号包裹。
    """
    return '{{' + remove_outer_braces(title) + '}}'


def process_journal_and_booktitle(entry, mapping):
    """
    对 entry 中的 journal 和 booktitle 字段进行处理，调用 process_field 进行替换。
    """
    for field in ['journal', 'booktitle']:
        if field in entry:
            # 对内部内容进行规范化处理
            normalized = normalize_string(entry[field])
            if normalized in mapping:
                entry[field] = mapping[normalized]
    return entry


def parse_aux(aux_path):
    # 从 .aux 文件中获取被引用的条目编号
    citations = {}
    with open(aux_path, 'r', encoding='utf-8') as aux_file:
        for line in aux_file:
            m = re.search(r"\\bibcite{([^}]+)}{(\d+)}", line)
            if m:
                key, num = m.groups()
                citations[key] = int(num)
    return citations


def parse_bib(bib_path):
    """将 .bib 文件按条目分割"""
    with open(bib_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 以行首 @ 符号分割（假设每个条目以 @ 开头）
    entries = re.split(r'\n(?=@)', content)
    entries_in_k_v = {}
    for entry in entries:
        # 进一步解析为各个键值对
        m = re.match(r'\s*@(?P<type>\w+)\{(?P<name>\w+),', entry, flags=re.IGNORECASE)
        if not m:
            continue
        type = m.groupdict()['type']
        name = m.groupdict()['name']
        entry_in_k_v = {'type': type}
        pos_in_src_entry = m.end()
        while True:
            if pos_in_src_entry > len(entry) + 1:
                print("\033[91mWarning!\033[0m")
                break
            m = re.match(r'\s*,?\s*(?P<key>\w+)\s*=\s*', entry[pos_in_src_entry:], flags=re.IGNORECASE)
            if not m:
                # reach the end
                m = re.match(r'\s*,?\s*}', entry[pos_in_src_entry:], flags=re.IGNORECASE)
                if m:
                    break
                else:
                    print("\033[91mWarning!\033[0m")
                    break
            else:
                key = m.groupdict()['key']
                pos_in_src_entry += (m.end())
                m = re.match(r'\s*\{', entry[pos_in_src_entry:], flags=re.IGNORECASE)
                if m:
                    # {...}
                    braced, end_pos = extract_braced(entry[pos_in_src_entry:], 0)
                    entry_in_k_v[key] = braced
                    pos_in_src_entry += (end_pos + 1)
                else:
                    # ...,
                    m = re.match(r'\s*(?P<value>\w+),', entry[pos_in_src_entry:], flags=re.IGNORECASE)
                    if m:
                        entry_in_k_v[key] = m.groupdict()['value']
                        pos_in_src_entry += (m.end() +1)
                    else:
                        print("\033[91mWarning: empty after '='!\033[0m")
                        break
        entries_in_k_v[name] = entry_in_k_v
        # pprint.pprint(entry_in_k_v)
    return entries_in_k_v

def filter_sort_deduplicate(entries_in_k_v, citations, mapping):
    """
    1. 保留在 .aux 文件中被引用的条目
    2. 去除重复条目（通过标准化文本）
    3. 对每个条目的 title、journal、booktitle 字段进行处理
    4. 按引用编号排序
    """
    for name in citations:
        if name not in entries_in_k_v:
            continue
        select_entry = entries_in_k_v[name]
        select_entry['title'] = process_title(select_entry['title'])
        entries_in_k_v[name] = process_journal_and_booktitle(select_entry, mapping)
    return entries_in_k_v


def write_bib(new_path, entries):
    """将处理后的条目写入新的 .bib 文件"""
    with open(new_path, 'w', encoding='utf-8') as f:
        for entry_name in entries:
            entry = entries[entry_name]
            f.write(f'@{entry['type']}{{{entry_name},\n')
            for key in entry:
                if key == 'type':
                    continue
                f.write(f'    {key}={entry[key]},\n')
            f.write('}\n\n')


# 示例调用，路径请根据实际文件修改：
ieee_path = r'xxx\IEEEfull.bib'

aux_path = r'xxx\rff_draft.aux'

# skip_date_check = True # 如果没有安装everything或者不想更新论文日期
skip_date_check = False   # 如果已经安装everything命令行版

es_cmd_path = r'xxx\es.exe'
# es_cmd_path = None        # 系统默认的everything路径

bib_path = r'xxxx\ref_test.bib'
new_bib_path = r'xxx\ref_test_2.bib'

# 从 .aux 文件中获取被引用的条目编号
citations = parse_aux(aux_path)
# 解析 IEEEfull.bib 得到映射字典
mapping = parse_ieee_mapping(ieee_path)
# 解析 .bib 文件
entries_in_k_v = parse_bib(bib_path)
# 过滤、去重、处理字段并排序
filtered_entries_in_k_v = filter_sort_deduplicate(entries_in_k_v, citations, mapping)
if not skip_date_check:
    # 更新论文日期
    new_entries = update_bib_year_and_month(filtered_entries_in_k_v, es_cmd_path)
else:
    new_entries = filtered_entries_in_k_v
write_bib(new_bib_path, new_entries)
print(f"新文件已生成: {new_bib_path}")
