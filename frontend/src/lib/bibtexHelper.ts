import { decodeOrdered } from './helperFunctions.js';

const STOPWORDS = new Set<string>([
"i",
"me",
"my",
"myself",
"we",
"our",
"ours",
"ourselves",
"you",
"your",
"yours",
"yourself",
"yourselves",
"he",
"him",
"his",
"himself",
"she",
"her",
"hers",
"herself",
"it",
"its",
"itself",
"they",
"them",
"their",
"theirs",
"themselves",
"what",
"which",
"who",
"whom",
"this",
"that",
"these",
"those",
"am",
"is",
"are",
"was",
"were",
"be",
"been",
"being",
"have",
"has",
"had",
"having",
"do",
"does",
"did",
"doing",
"a",
"an",
"the",
"and",
"but",
"if",
"or",
"because",
"as",
"until",
"while",
"of",
"at",
"by",
"for",
"with",
"about",
"against",
"between",
"into",
"through",
"during",
"before",
"after",
"above",
"below",
"to",
"from",
"up",
"down",
"in",
"out",
"on",
"off",
"over",
"under",
"again",
"further",
"then",
"once",
"here",
"there",
"when",
"where",
"why",
"how",
"all",
"any",
"both",
"each",
"few",
"more",
"most",
"other",
"some",
"such",
"no",
"nor",
"not",
"only",
"own",
"same",
"so",
"than",
"too",
"very",
"s",
"t",
"can",
"will",
"just",
"don",
"should",
"now",
]);

const BIBTEX_CHAR_MAP: Record<string, string> = {
    // Umlaut / diaeresis
    'ä': '\\"{a}', 'ö': '\\"{o}', 'ü': '\\"{u}',
    'Ä': '\\"{A}', 'Ö': '\\"{O}', 'Ü': '\\"{U}',
    'ë': '\\"{e}', 'ï': '\\"{i}', 'ÿ': '\\"{y}',
    'Ë': '\\"{E}', 'Ï': '\\"{I}',
    // Acute
    'á': "\\'{a}", 'é': "\\'{e}", 'í': "\\'{i}", 'ó': "\\'{o}", 'ú': "\\'{u}", 'ý': "\\'{y}",
    'Á': "\\'{A}", 'É': "\\'{E}", 'Í': "\\'{I}", 'Ó': "\\'{O}", 'Ú': "\\'{U}", 'Ý': "\\'{Y}",
    'ś': "\\'{s}", 'ź': "\\'{z}", 'ń': "\\'{n}", 'ć': "\\'{c}",
    'Ś': "\\'{S}", 'Ź': "\\'{Z}", 'Ń': "\\'{N}", 'Ć': "\\'{C}",
    // Grave
    'à': '\\`{a}', 'è': '\\`{e}', 'ì': '\\`{i}', 'ò': '\\`{o}', 'ù': '\\`{u}',
    'À': '\\`{A}', 'È': '\\`{E}', 'Ì': '\\`{I}', 'Ò': '\\`{O}', 'Ù': '\\`{U}',
    // Circumflex
    'â': '\\^{a}', 'ê': '\\^{e}', 'î': '\\^{i}', 'ô': '\\^{o}', 'û': '\\^{u}',
    'Â': '\\^{A}', 'Ê': '\\^{E}', 'Î': '\\^{I}', 'Ô': '\\^{O}', 'Û': '\\^{U}',
    // Tilde
    'ã': '\\~{a}', 'ñ': '\\~{n}', 'õ': '\\~{o}',
    'Ã': '\\~{A}', 'Ñ': '\\~{N}', 'Õ': '\\~{O}',
    // Cedilla
    'ç': '\\c{c}', 'Ç': '\\c{C}',
    // Eszett
    'ß': '{\\ss}',
    // Scandinavian
    'ø': '{\\o}', 'Ø': '{\\O}',
    'å': '{\\aa}', 'Å': '{\\AA}',
    'æ': '{\\ae}', 'Æ': '{\\AE}',
    // Polish l-stroke
    'ł': '{\\l}', 'Ł': '{\\L}',
    // Caron / háček
    'š': '\\v{s}', 'č': '\\v{c}', 'ž': '\\v{z}', 'ř': '\\v{r}',
    'ě': '\\v{e}', 'ď': '\\v{d}', 'ť': '\\v{t}', 'ň': '\\v{n}',
    'Š': '\\v{S}', 'Č': '\\v{C}', 'Ž': '\\v{Z}', 'Ř': '\\v{R}',
    'Ě': '\\v{E}', 'Ď': '\\v{D}', 'Ť': '\\v{T}', 'Ň': '\\v{N}',
    // Ogonek
    'ą': '\\k{a}', 'ę': '\\k{e}', 'Ą': '\\k{A}', 'Ę': '\\k{E}',
    // Dot above
    'ż': '\\.{z}', 'Ż': '\\.{Z}',
    // Double acute
    'ő': '\\H{o}', 'ű': '\\H{u}', 'Ő': '\\H{O}', 'Ű': '\\H{U}',
    // Ring above
    'ů': '\\r{u}', 'Ů': '\\r{U}',
}

const BIBTEX_CHAR_REGEX = new RegExp(
    Object.keys(BIBTEX_CHAR_MAP).map(c => c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'),
    'g'
)

export function escapeBibtex(str: string): string {
    return str.replace(BIBTEX_CHAR_REGEX, char => BIBTEX_CHAR_MAP[char] ?? char)
}

export function createBibtexString(data): string{
    let str = ""
    const bibtexType = data.bibtexType.split("#").at(-1)
    if(bibtexType === "Inproceedings"){
        str = createInproceedingsString(data)
    }else if(bibtexType === "Proceedings"){
        str = createProceedingsString(data)
    }else if(bibtexType === "Article"){
        str = createArticleString(data)
    }
    str = escapeBibtex(str)
    return str
}

function createInproceedingsString(data): string{
    let bibtexString = "@inproceedings{"+createBibtexKey(data)+"\n"
    const authors = decodeOrdered(data.authors, true)
    bibtexString += "author     = {" + authors[0]
    for(let i = 1; i < authors.length; i++){
        bibtexString += " and \n" + authors[i]
    }
    bibtexString += "},\n"

    if(data.editors !== null){
        const editors = decodeOrdered(data.editors, true)
        bibtexString += "editor     = {" + editors[0]
        for(let i = 1; i < editors.length; i++){
            bibtexString += " and \n" + editors[i]
        }
        bibtexString += "},\n"
    }
    bibtexString += "title      = {" + escapeBibtex(data.title) + "},\n"
    bibtexString += "booktitle  = {" + escapeBibtex(data.booktitle) + "},\n"
    if(data.series !== null){bibtexString += "series  = {" + escapeBibtex(data.series) + "},\n"}
    if(data.pages !== null){bibtexString += "pages  = {" + data.pages + "},\n"}
    if(data.publisher !== null){bibtexString += "publisher  = {" + escapeBibtex(data.publisher) + "},\n"}
    bibtexString += "year  = {" + data.year + "},\n"
    if(data.month !== null){bibtexString += "month  = {" + data.month + "},\n"}
    if(data.url !== null){bibtexString += "url  = {" + data.url + "},\n"}
    if(data.doi !== null){bibtexString += "doi  = {" + data.doi + "},\n"}

    bibtexString += "}"
    return bibtexString
}

function createProceedingsString(data): string{
    let bibtexString = "@proceedings{"+createBibtexKey(data)+"\n"

    if(data.editors !== null){
        const editors = decodeOrdered(data.editors, true)
        bibtexString += "editor     = {" + editors[0]
        for(let i = 1; i < editors.length; i++){
            bibtexString += " and \n" + editors[i] 
        }
        bibtexString += "},\n"
    }

    bibtexString += "title      = {" + data.title + "}\n"
    if(data.series !== null){bibtexString += "series  = {" + data.series + "}\n"}
    if(data.volume !== null){bibtexString += "volume  = {" + data.volume + "}\n"}
    if(data.publisher !== null){bibtexString += "publisher  = {" + data.publisher + "}\n"}
    bibtexString += "year  = {" + data.year + "}\n"
    if(data.month !== null){bibtexString += "month  = {" + data.month + "}\n"}
    if(data.url !== null){bibtexString += "url  = {" + data.url + "}\n"}
    if(data.doi !== null){bibtexString += "doi  = {" + data.doi + "}\n"}
    if(data.isbn !== null){bibtexString += "isbn  = {" + data.isbn + "}\n"}

    bibtexString += "}"
    return bibtexString
}

function createArticleString(data): string{
    let bibtexString = "@article{"+createBibtexKey(data)+",\n"
    const authors = decodeOrdered(data.authors, true)
    bibtexString += "author     = {" + authors[0]
    for(let i = 1; i < authors.length; i++){
        bibtexString += " and \n" + authors[i]
    }
    bibtexString += "},\n"

    bibtexString += "title      = {" + data.title + "}\n"
    bibtexString += "journal  = {" + data.streamTitle + "}\n"
    if(data.volume !== null){bibtexString += "volume  = {" + data.volume + "}\n"}
    if(data.number !== null){bibtexString += "number  = {" + data.number + "}\n"}
    if(data.pages !== null){bibtexString += "pages  = {" + data.pages + "}\n"}
    bibtexString += "year  = {" + data.year + "}\n"
    if(data.url !== null){bibtexString += "url  = {" + data.url + "}\n"}
    if(data.doi !== null){bibtexString += "doi  = {" + data.doi + "}\n"}

    bibtexString += "}"
    return bibtexString
}

function simplifyForKey(str: string): string {
    return str
        .replace(/ß/g, 'ss')
        .replace(/æ/gi, 'ae')
        .replace(/œ/gi, 'oe')
        .replace(/ø/gi, 'o')
        .replace(/ł/gi, 'l')
        .normalize('NFD')
        .replace(/\p{M}/gu, '')
}

function createBibtexKey(data: Record<string, string | null>){
    let creator;
    if(data.authors !== null){
        const authors = decodeOrdered(data.authors, true)
        creator = removeSpecialCharacters(simplifyForKey(authors[0]?.split(" ").at(-1)?.toLowerCase() ?? ''))
    }else{
        const editors = (data.editors ?? '').split(",")
        creator = removeSpecialCharacters(simplifyForKey(editors[0]?.split(" ").at(-1)?.toLowerCase() ?? ''))
    }

    const title = removeSpecialCharacters(simplifyForKey((data.title ?? '').toLowerCase()))
        .split(' ')
        .filter((word: string) => word && !STOPWORDS.has(word))
        .join(' ')

    return creator+"-"+data.year+"-"+title.split(" ")[0]
}

function removeSpecialCharacters(str: string) {
  return str.replace(/[^a-zA-Z0-9 ]/g, "");
}