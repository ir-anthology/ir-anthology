import { fetchDataForConferenceYear, fetchDataForInproceedingsFromProceedings, fetchDataForJournalYear } from '$lib/sparql/fetch.server.js'
import { parseSparqlResult, getURIFromID, getIDFromURI } from '$lib/helperFunctions.js';
export async function load({params}) {
    const name = params.name
    const uri = getURIFromID(name) 
    const year = params.year
    if(name.includes("conf")){
        return loadConference(uri, year)
    }else if(name.includes("journals")){
        return loadJournal(uri, year)
    }
}

async function loadConference(uri: string, year: string){
    const data = await fetchDataForConferenceYear(uri, year);
    // const binding = data.bindings[0];
    let titles = ''
    const proceedings = parseSparqlResult(data);
    for(const proceeding of proceedings){
        titles += '\n<'+(proceeding.pub)+'>'
    }
    const inproceedingsData = await fetchDataForInproceedingsFromProceedings(titles);
    const inproceedings = parseSparqlResult(inproceedingsData);
    const return_inproceedings:Record<string, Record<string, string | null>[]> = {};
    for(const inproceeding of inproceedings){
        const book = inproceeding.book;
        if(book === null){ continue; }
        if (!(book in return_inproceedings)){
            return_inproceedings[book] = [];
        }
        inproceeding["id"] = getIDFromURI(inproceeding.pub)
        return_inproceedings[book].push(inproceeding)
    }
    return {"proceedings": proceedings, "inproceedings": return_inproceedings};
}

async function loadJournal(uri:string, year:string){
    const data = parseSparqlResult(await fetchDataForJournalYear(uri, year))
    const journalTitle = data[0]?.journalTitle ?? ''
    const groupedData = new Map<string, Map<string, Record<string, string | null>[]>>();
    for(const entry of data){
        const volume = entry.volume;
        const issue = entry.number;
        if(volume === null || issue === null){ continue; }
        if(!groupedData.has(volume)){
            groupedData.set(volume, new Map<string, Record<string, string>[]>())
        }
        if(!groupedData.get(volume)?.has(issue)){
            groupedData.get(volume)?.set(issue, [])
        }
        groupedData.get(volume)?.get(issue)?.push(entry)
    }
    return { articles: groupedData, journalTitle }
}