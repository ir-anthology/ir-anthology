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

export function createBibTeXString(data): string{
    const bibtexType = data.bibtexType.split("#").at(-1)
    if(bibtexType === "Inproceedings"){
        return createInproceedingsString(data)
    }else if(bibtexType === "Proceedings"){
        return createProceedingsString(data)
    }else if(bibtexType === "Article"){
        return createArticleString(data)
    }
    return ""
}

function createInproceedingsString(data): string{
    let bibtexString = "@inproceedings{"+createBibteXKey(data)+"\n"
    const authors = data.authors.split(",")
    bibtexString += "author     = {" + authors[0]
    for(let i = 1; i < authors.length; i++){
        bibtexString += " and \n" + authors[i] 
    }
    bibtexString += "},\n"

    if(data.editors !== null){
        const editors = data.editors.split(",")
        bibtexString += "editor     = {" + editors[0]
        for(let i = 1; i < editors.length; i++){
            bibtexString += " and \n" + editors[i] 
        }
        bibtexString += "},\n"
    }
    bibtexString += "title      = {" + data.title + "}\n"
    bibtexString += "booktitle  = {" + data.booktitle + "}\n"
    if(data.series !== null){bibtexString += "series  = {" + data.series + "}\n"}
    if(data.pages !== null){bibtexString += "pages  = {" + data.pages + "}\n"}
    if(data.publisher !== null){bibtexString += "publisher  = {" + data.publisher + "}\n"}
    bibtexString += "year  = {" + data.year + "}\n"
    if(data.month !== null){bibtexString += "month  = {" + data.month + "}\n"}
    if(data.url !== null){bibtexString += "url  = {" + data.url + "}\n"}
    if(data.doi !== null){bibtexString += "doi  = {" + data.doi + "}\n"}

    bibtexString += "}"
    return bibtexString
}

function createProceedingsString(data): string{
    let bibtexString = "@proceedings{"+createBibteXKey(data)+"\n"

    if(data.editors !== null){
        const editors = data.editors.split(",")
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
    let bibtexString = "@article{"+createBibteXKey(data)+"\n"
    const authors = data.authors.split(",")
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

function createBibteXKey(data){
    let creator;
    if(data.authors !== null){
        const authors = data.authors.split(",")
        creator = authors[0].split(" ").at(-1).toLowerCase()
    }else{
        const editors = data.editors.split(",")
        creator = editors[0].split(" ").at(-1).toLowerCase()
    }
    
    const title = removeSpecialCharacters(data.title.toLowerCase())
    .split(' ')
    .filter(word => word && !STOPWORDS.has(word))
    .join(' ')


    return creator+"-"+data.year+"-"+title.split(" ")[0]
}

function removeSpecialCharacters(str) {
  return str.replace(/[^a-zA-Z0-9 ]/g, "");
}