# -*- coding: utf-8 -*-
import re
import subprocess
import time

import PyPDF2
import os


# Month mapping table
MONTH_MAP = {
    'january': 'jan', 'february': 'feb', 'march': 'mar', 'april': 'apr',
    'june': 'jun', 'july': 'jul', 'august': 'aug',
    'september': 'sep', 'october': 'oct', 'november': 'nov', 'december': 'dec',
    'jan': 'jan', 'feb': 'feb', 'mar': 'mar', 'apr': 'apr',
    'may': 'may', 'jun': 'jun', 'jul': 'jul', 'aug': 'aug',
    'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dec': 'dec'
}

# refer to https://github.com/marcinwrochna/abbrevIso/blob/master/shortwords.txt
short_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'so', 'yet', 'though', 'when', 'whenever', 'where',
                'whereas', 'wherever', 'while', 'about', 'afore', 'after', 'ago', 'along', 'amid', 'among', 'amongst',
                'apropos', 'as', 'at', 'atop', 'but', 'by', 'ca', 'circa', 'for', 'from', 'hence', 'in', 'into', 'like',
                'of', 'off', 'on', 'onto', 'ontop', 'out', 'over', 'per', 'since', 'than', 'til', 'till', 'to', 'unlike',
                'until', 'unto', 'up', 'upon', 'upside', 'versus', 'via', 'vis-a-vis', 'vs', 'with', 'within', 'für',
                'und', 'aus', 'zu', 'zur', 'im', 'de', 'et', 'y', 'del', 'en', 'di', 'e', 'da', 'delle', 'della',
                'dello', 'degli', 'sue', 'el', 'do', 'og', 'i', 'voor', 'van', "dell'", 'dell', 'ed', 'för', 'tot',
                'vir', 'o', 'its', 'sul',
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
    Normalize string s by removing braces, standardizing whitespace for fuzzy matching.
    Not converting to lowercase !!!
    """
    no_braces = re.sub(r'[{}]', '', s)
    normalized = ' '.join(no_braces.split())
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
        normalized_full = normalize_string(full_name).lower()
        mapping[normalized_full] = string_entry
        pos = i + 1

    return mapping


def parse_ITWA_word_mapping(word_addr_csv_path):
    with open(word_addr_csv_path, mode='r', encoding='utf-8') as f:
        res = f.read()

    res2 = res.splitlines()
    word_str_to_pattern_and_mapping = {}
    for line in res2:
        if line.startswith('WORD'):
            continue
        r3 = line.split('\t')
        assert len(r3) == 3
        word_str, new_word, _ = r3
        if word_str in word_str_to_pattern_and_mapping:
            print("warning! duplicate:", word_str)
        if word_str.startswith('-'):
            # not required to match the beginning of a word
            pattern = re.compile(rf'(?<=\w){word_str[1:]}$')
            if new_word.startswith('-'):
                new_word = new_word[1:]
        elif word_str.endswith('-'):
            pattern = re.compile(rf'^{word_str[:-1]}\w+$')
        else:
            pattern = re.compile(rf'^{word_str}$')
        if new_word != "":
            word_str_to_pattern_and_mapping[word_str] = [pattern, new_word]
        else:
            # means not change this word.
            # (this is not redundant because this word may be matched by other patterns by false)
            word_str_to_pattern_and_mapping[word_str] = [pattern, word_str]
    return word_str_to_pattern_and_mapping

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

def perform_word_mapping(word_mapping, word):
    """
    Process a word of journal and booktitle names using word_mapping.
    If not match, return  None.
    """
    match_length = 0
    new_word = None
    for key_word_str in word_mapping:
        _pattern, new_str = word_mapping[key_word_str]
        tmp_new_word, count = _pattern.subn(new_str, word)
        # using the longest match
        if count > 0 and len(key_word_str) > match_length:
            match_length = len(key_word_str)
            new_word = tmp_new_word
    if new_word:
        return new_word[0].upper() + new_word[1:]
    else:
        return new_word

def process_journal_booktitle(entry, journal_mapping, word_mapping):
    """
    Process journal and booktitle fields in an entry by replacing with abbreviations using mapping.
    """
    for field in ['journal', 'booktitle']:
        if field in entry:
            if not entry[field].startswith('{'):
                # something like IEEE_J_AC
                continue
            normalized = normalize_string(entry[field])
            if normalized.lower() in journal_mapping:
                # IEEE journal mapping
                entry[field] = journal_mapping[normalized.lower()]
            else:
                # word mapping
                words = normalized.split(" ")
                new_words = []
                for i, word_i in enumerate(words):
                    # start_time = time.time()
                    if word_i.lower() in short_words:
                        continue
                    new_word = perform_word_mapping(word_mapping=word_mapping, word=word_i.lower())
                    if new_word:
                        new_words.append(new_word)
                    else:
                        new_words.append(word_i[0].upper() + word_i[1:])
                    # print(f"cost {time.time() - start_time:.1f} s")
                entry[field] = '{{' + " ".join(new_words) + '}}'
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
        m = re.match(r'\s*@(?P<__type>\S+)\{(?P<name>\S+),', entry, flags=re.IGNORECASE)
        if not m:
            continue
        type = m.groupdict()['__type']
        name = m.groupdict()['name']
        entry_in_k_v = {'__type': type}
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

def filter_sort_deduplicate(entries_in_k_v, citations, journal_mapping, word_mapping):
    """
    1. Keep entries cited in .aux file
    2. Remove duplicates via normalized text
    3. Process title, journal, and booktitle fields
    4. Sort by citation number
    """
    filtered_entries_in_k_v = {}
    for name in citations:
        if name not in entries_in_k_v:
            print(f"\033[91mWarning: Citation:{name} not found in .bib!\033[0m")
            continue
        select_entry = filtered_entries_in_k_v[name] = entries_in_k_v[name]
        select_entry['title'] = process_title(select_entry['title'])
        filtered_entries_in_k_v[name] = process_journal_booktitle(select_entry, journal_mapping=journal_mapping,
                                                                  word_mapping=word_mapping)
        # add "Proc." to proceedings
        # & remove the year in booktitle
        if select_entry['__type'] == 'inproceedings':
            if 'booktitle' in select_entry:
                # 替换四位数字（年份）
                _title = re.sub(r'\b\d{4}\b', '', select_entry['booktitle'])
                _title2 = normalize_string(_title)
                if not _title2.startswith('Proc.'):
                    select_entry['booktitle'] = '{{Proc. ' + _title2 + '}}'
                else:
                    select_entry['booktitle'] = '{{' + _title2 + '}}'
            else:
                print(f"\033[91mWarning: 'booktitle' not found in this 'inproceeding' entry\033[0m")
            pass
            # if select_entry['booktitle']
    return filtered_entries_in_k_v


def write_bib(new_path, entries):
    """Write processed entries to a new .bib file"""
    with open(new_path, 'w', encoding='utf-8') as f:
        for entry_name in entries:
            entry = entries[entry_name]
            f.write(f'@{entry['__type']}{{{entry_name},\n')
            for key in entry:
                if key == '__type':
                    continue
                f.write(f'    {key}={re.sub(r'\s+', ' ', entry[key])},\n')
            f.write('}\n\n')



def process_files(aux_path, ieee_full_bib_path, word_addr_csv_path, bib_path, skip_date_check, es_cmd_path, new_bib_path):

    # Extract cited entries from .aux file
    citations = parse_aux(aux_path)

    # Parse IEEEfull.bib to build abbreviation mapping
    journal_mapping = parse_ieee_mapping(ieee_full_bib_path)

    #
    start_time = time.time()
    word_mapping = parse_ITWA_word_mapping(word_addr_csv_path)
    print(f"parse_ITWA_word_mapping cost {time.time() - start_time:.1f} s")

    # Parse .bib file
    entries_in_k_v = parse_bib(bib_path)

    # Filter, deduplicate, process fields, and sort
    filtered_entries_in_k_v = filter_sort_deduplicate(entries_in_k_v, citations,
                                                      journal_mapping=journal_mapping,
                                                      word_mapping=word_mapping)
    if not skip_date_check:
        # Update citation dates
        new_entries = update_bib_year_and_month(filtered_entries_in_k_v, es_cmd_path)
    else:
        new_entries = filtered_entries_in_k_v
    write_bib(new_bib_path, new_entries)
    print(f"New file generated: {new_bib_path}")

