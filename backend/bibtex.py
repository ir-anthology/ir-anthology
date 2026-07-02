import re
import unicodedata

STOPWORDS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your","yours",
    "yourself","yourselves","he","him","his","himself","she","her","hers",
    "herself","it","its","itself","they","them","their","theirs","themselves",
    "what","which","who","whom","this","that","these","those","am","is","are",
    "was","were","be","been","being","have","has","had","having","do","does",
    "did","doing","a","an","the","and","but","if","or","because","as","until",
    "while","of","at","by","for","with","about","against","between","into",
    "through","during","before","after","above","below","to","from","up","down",
    "in","out","on","off","over","under","again","further","then","once","here",
    "there","when","where","why","how","all","any","both","each","few","more",
    "most","other","some","such","no","nor","not","only","own","same","so",
    "than","too","very","s","t","can","will","just","don","should","now",
}

BIBTEX_CHAR_MAP: dict[str, str] = {
    'ä': '\\"{a}', 'ö': '\\"{o}', 'ü': '\\"{u}',
    'Ä': '\\"{A}', 'Ö': '\\"{O}', 'Ü': '\\"{U}',
    'ë': '\\"{e}', 'ï': '\\"{i}', 'ÿ': '\\"{y}',
    'Ë': '\\"{E}', 'Ï': '\\"{I}',
    'á': "\\'{a}", 'é': "\\'{e}", 'í': "\\'{i}", 'ó': "\\'{o}", 'ú': "\\'{u}", 'ý': "\\'{y}",
    'Á': "\\'{A}", 'É': "\\'{E}", 'Í': "\\'{I}", 'Ó': "\\'{O}", 'Ú': "\\'{U}", 'Ý': "\\'{Y}",
    'ś': "\\'{s}", 'ź': "\\'{z}", 'ń': "\\'{n}", 'ć': "\\'{c}",
    'Ś': "\\'{S}", 'Ź': "\\'{Z}", 'Ń': "\\'{N}", 'Ć': "\\'{C}",
    'à': '\\`{a}', 'è': '\\`{e}', 'ì': '\\`{i}', 'ò': '\\`{o}', 'ù': '\\`{u}',
    'À': '\\`{A}', 'È': '\\`{E}', 'Ì': '\\`{I}', 'Ò': '\\`{O}', 'Ù': '\\`{U}',
    'â': '\\^{a}', 'ê': '\\^{e}', 'î': '\\^{i}', 'ô': '\\^{o}', 'û': '\\^{u}',
    'Â': '\\^{A}', 'Ê': '\\^{E}', 'Î': '\\^{I}', 'Ô': '\\^{O}', 'Û': '\\^{U}',
    'ã': '\\~{a}', 'ñ': '\\~{n}', 'õ': '\\~{o}',
    'Ã': '\\~{A}', 'Ñ': '\\~{N}', 'Õ': '\\~{O}',
    'ç': '\\c{c}', 'Ç': '\\c{C}',
    'ß': '{\\ss}',
    'ø': '{\\o}', 'Ø': '{\\O}',
    'å': '{\\aa}', 'Å': '{\\AA}',
    'æ': '{\\ae}', 'Æ': '{\\AE}',
    'ł': '{\\l}', 'Ł': '{\\L}',
    'š': '\\v{s}', 'č': '\\v{c}', 'ž': '\\v{z}', 'ř': '\\v{r}',
    'ě': '\\v{e}', 'ď': '\\v{d}', 'ť': '\\v{t}', 'ň': '\\v{n}',
    'Š': '\\v{S}', 'Č': '\\v{C}', 'Ž': '\\v{Z}', 'Ř': '\\v{R}',
    'Ě': '\\v{E}', 'Ď': '\\v{D}', 'Ť': '\\v{T}', 'Ň': '\\v{N}',
    'ą': '\\k{a}', 'ę': '\\k{e}', 'Ą': '\\k{A}', 'Ę': '\\k{E}',
    'ż': '\\.{z}', 'Ż': '\\.{Z}',
    'ő': '\\H{o}', 'ű': '\\H{u}', 'Ő': '\\H{O}', 'Ű': '\\H{U}',
    'ů': '\\r{u}', 'Ů': '\\r{U}',
}


def _normalize_pages(s: str) -> str:
    return re.sub(r'-+', '--', s)


def escape_bibtex(s: str) -> str:
    return ''.join(BIBTEX_CHAR_MAP.get(c, c) for c in (s or ''))


def decode_ordered(raw: str | None, strip_disambig: bool = False) -> list[str]:
    if not raw:
        return []
    entries = []
    for entry in raw.split(', '):
        sep = entry.find('@@')
        if sep == -1:
            entries.append((0, entry))
            continue
        value = entry[sep + 2:]
        if strip_disambig:
            value = re.sub(r'\s+\d+$', '', value)
        entries.append((int(entry[:sep]), value))
    entries.sort(key=lambda x: x[0])
    return [v for _, v in entries]


def _simplify_for_key(s: str) -> str:
    for src, dst in [('ß','ss'),('æ','ae'),('Æ','AE'),('œ','oe'),('Œ','OE'),('ø','o'),('Ø','O'),('ł','l'),('Ł','L')]:
        s = s.replace(src, dst)
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()


def _remove_special(s: str) -> str:
    return re.sub(r'[^a-zA-Z0-9 ]', '', s)


def _bibtex_key(data: dict) -> str:
    if data.get('authors'):
        authors = decode_ordered(data['authors'], strip_disambig=True)
        last = (authors[0].split(' ')[-1] if authors else '').lower()
    else:
        editors = (data.get('editors') or '').split(',')
        last = (editors[0].split(' ')[-1] if editors else '').lower()
    creator = _remove_special(_simplify_for_key(last))
    title_words = _remove_special(_simplify_for_key((data.get('title') or '').lower())).split()
    first_content = next((w for w in title_words if w not in STOPWORDS), '')
    return f"{creator}-{data.get('year', '')}-{first_content}"


def bindings_to_dict(vars: list[str], bindings: list[dict]) -> dict:
    if not bindings:
        return {}
    return {k: (bindings[0][k]['value'] if k in bindings[0] else None) for k in vars}


def _format_entry(entry_type: str, key: str, fields: list[tuple[str, str]]) -> str:
    width = max(len(f) for f, _ in fields)
    # prefix before value: "  {field:<width} = {" = 2 + width + 4 chars
    cont_indent = ' ' * (2 + width + 4)
    lines = [f"@{entry_type}{{{key},"]
    for i, (field, value) in enumerate(fields):
        comma = "," if i < len(fields) - 1 else ""
        value_indented = value.replace('\n', f'\n{cont_indent}')
        lines.append(f"  {field:<{width}} = {{{value_indented}}}{comma}")
    lines.append("}")
    return "\n".join(lines)


def create_bibtex(data: dict) -> str:
    bibtex_type = (data.get('bibtexType') or '').split('#')[-1]
    if bibtex_type == 'Inproceedings':
        return escape_bibtex(_inproceedings(data))
    if bibtex_type == 'Proceedings':
        return escape_bibtex(_proceedings(data))
    if bibtex_type == 'Article':
        return escape_bibtex(_article(data))
    return ''


def _inproceedings(data: dict) -> str:
    authors = decode_ordered(data.get('authors'), strip_disambig=True)
    fields: list[tuple[str, str]] = [('author', ' and\n'.join(authors))]
    if data.get('editors'):
        editors = decode_ordered(data.get('editors'), strip_disambig=True)
        fields.append(('editor', ' and\n'.join(editors)))
    fields.append(('title', '{' + data.get('title', '') + '}'))
    fields.append(('booktitle', '{' + data.get('booktitle', '') + '}'))
    if data.get('series'):    fields.append(('series', data['series']))
    if data.get('volume'):    fields.append(('volume', data['volume']))
    if data.get('pages'):     fields.append(('pages', _normalize_pages(data['pages'])))
    if data.get('publisher'): fields.append(('publisher', data['publisher']))
    fields.append(('year', data.get('year', '')))
    if data.get('month'):     fields.append(('month', data['month']))
    if data.get('url'):       fields.append(('url', data['url']))
    if data.get('doi'):       fields.append(('doi', data['doi']))
    return _format_entry('inproceedings', _bibtex_key(data), fields)


def _proceedings(data: dict) -> str:
    fields: list[tuple[str, str]] = []
    if data.get('editors'):
        editors = decode_ordered(data.get('editors'), strip_disambig=True)
        fields.append(('editor', ' and\n'.join(editors)))
    fields.append(('title', '{' + data.get('title', '') + '}'))
    if data.get('series'):    fields.append(('series', data['series']))
    if data.get('volume'):    fields.append(('volume', data['volume']))
    if data.get('publisher'): fields.append(('publisher', data['publisher']))
    fields.append(('year', data.get('year', '')))
    if data.get('month'):     fields.append(('month', data['month']))
    if data.get('url'):       fields.append(('url', data['url']))
    if data.get('doi'):       fields.append(('doi', data['doi']))
    if data.get('isbn'):      fields.append(('isbn', data['isbn']))
    return _format_entry('proceedings', _bibtex_key(data), fields)


def _article(data: dict) -> str:
    authors = decode_ordered(data.get('authors'), strip_disambig=True)
    fields: list[tuple[str, str]] = [('author', ' and\n'.join(authors))]
    fields.append(('title', '{' + data.get('title', '') + '}'))
    fields.append(('journal', data.get('streamTitle', '')))
    if data.get('volume'):    fields.append(('volume', data['volume']))
    if data.get('number'):    fields.append(('number', data['number']))
    if data.get('pages'):     fields.append(('pages', _normalize_pages(data['pages'])))
    fields.append(('year', data.get('year', '')))
    if data.get('url'):       fields.append(('url', data['url']))
    if data.get('doi'):       fields.append(('doi', data['doi']))
    return _format_entry('article', _bibtex_key(data), fields)
