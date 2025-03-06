import pprint
import re
import os
import re
import subprocess
from datetime import datetime
import PyPDF2

# Month mapping table
MONTH_MAP = {
    'january': 'jan', 'february': 'feb', 'march': 'mar', 'april': 'apr',
    'june': 'jun', 'july': 'jul', 'august': 'aug',
    'september': 'sep', 'october': 'oct', 'november': 'nov', 'december': 'dec',
    'jan': 'jan', 'feb': 'feb', 'mar': 'mar', 'apr': 'apr',
    'may': 'may', 'jun': 'jun', 'jul': 'jul', 'aug': 'aug',
    'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dec': 'dec'
}

# Extract date information from PDF
def extract_date_from_pdf(pdf_path):
    try:
        print('try:', pdf_path)
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            # only extract from the first page
            for page in reader.pages:
                if page.extract_text():
                    src_text = page.extract_text()
                    break

        # Replace all consecutive whitespace characters with a single space  
        text = re.sub(r'\s+', ' ', src_text)
        # print(text)

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


# Search PDF file paths using Everything and extract dates
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


# Main program
def update_bib_year_and_month(entries, es_cmd_path):
    # entries : {'alice2000':{}, }
    skip_all = False
    auto_run_all = False
    for entry_name in entries:
        entry = entries[entry_name]
        if not skip_all:
            # Replace non-alphabetic characters with a space
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
    Extract the outermost braced content from text starting at start_index (assumed to be '{').
    Returns (braced_string, end_index); braced_string includes the outermost braces.
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
    Normalize string s by removing braces, standardizing whitespace, and converting to lowercase for fuzzy matching.
    """
    no_braces = re.sub(r'[{}]', '', s)
    normalized = ' '.join(no_braces.split()).lower()
    return normalized

def parse_ieee_mapping(ieee_path):
    """
    Parse mappings from IEEEfull.bib:
        key : Normalized journal full name (braces removed, whitespace standardized, lowercase)
        value : Corresponding abbreviation (e.g., IEEE_J_WCOM)
    Assumes entries in IEEEfull.bib are formatted as:
    @STRING{IEEE_J_WCOM = "{IEEE} Transactions on Wireless Communications"}
    """
    mapping = {}
    with open(ieee_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # Use regex to find @STRING{ ... =
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
    # Remove outermost paired braces from string
    pattern = r'^\{\s*(.*?)\s*\}$'
    while True:
        match = re.match(pattern, s)
        if match:
            s = match.group(1)  # Extract inner content
        else:
            break
    return s

def process_title(title):
    """
    Process the title field in an entry:
    Find the first '{' after "title=" and its matching outermost '}'.
    If the inner content is not wrapped in double braces, add double braces.
    """
    return '{{' + remove_outer_braces(title) + '}}'


def process_journal_and_booktitle(entry, mapping):
    """
    Process journal and booktitle fields in an entry by replacing with abbreviations using mapping.
    """
    for field in ['journal', 'booktitle']:
        if field in entry:
            normalized = normalize_string(entry[field])
            if normalized in mapping:
                entry[field] = mapping[normalized]
    return entry


def parse_aux(aux_path):
    # Extract cited entry keys from .aux file
    citations = {}
    with open(aux_path, 'r', encoding='utf-8') as aux_file:
        for line in aux_file:
            m = re.search(r"\\bibcite{([^}]+)}{(\d+)}", line)
            if m:
                key, num = m.groups()
                citations[key] = int(num)
    return citations


def parse_bib(bib_path):
    """Split .bib file into individual entries"""
    with open(bib_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Split by lines starting with @ (assumes entries start with @)
    entries = re.split(r'\n(?=@)', content)
    entries_in_k_v = {}
    for entry in entries:
        # Parse into key-value pairs
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
    1. Keep entries cited in .aux file
    2. Remove duplicates via normalized text
    3. Process title, journal, and booktitle fields
    4. Sort by citation number
    """
    for name in citations:
        if name not in entries_in_k_v:
            continue
        select_entry = entries_in_k_v[name]
        select_entry['title'] = process_title(select_entry['title'])
        entries_in_k_v[name] = process_journal_and_booktitle(select_entry, mapping)
    return entries_in_k_v


def write_bib(new_path, entries):
    """Write processed entries to a new .bib file"""
    with open(new_path, 'w', encoding='utf-8') as f:
        for entry_name in entries:
            entry = entries[entry_name]
            f.write(f'@{entry['type']}{{{entry_name},\n')
            for key in entry:
                if key == 'type':
                    continue
                f.write(f'    {key}={entry[key]},\n')
            f.write('}\n\n')


#Example usage (modify paths according to actual files):

ieee_path = r'your/path/IEEEfull.bib'
aux_path = r'your/path/your_project.aux'
bib_path = r'your/path/original.bib'
new_bib_path = r'your/path/updated.bib'

# Enable if Everything is not installed or date update is not needed
# skip_date_check = True 
# Enable if Everything is installed
skip_date_check = False  

es_cmd_path = r'your/path/es.exe'
# es_cmd_path = None        # Use default Everything path


# Extract cited entries from .aux file
citations = parse_aux(aux_path)

# Parse IEEEfull.bib to build abbreviation mapping
mapping = parse_ieee_mapping(ieee_path)

# Parse .bib file
entries_in_k_v = parse_bib(bib_path)

# Filter, deduplicate, process fields, and sort
filtered_entries_in_k_v = filter_sort_deduplicate(entries_in_k_v, citations, mapping)
if not skip_date_check:
    # Update citation dates
    new_entries = update_bib_year_and_month(filtered_entries_in_k_v, es_cmd_path)
else:
    new_entries = filtered_entries_in_k_v
write_bib(new_bib_path, new_entries)
print(f"New file generated: {new_bib_path}")
