import { fetchBackend } from '$lib/sparql/fetch.server.js'
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions.js';
export async function load({params}) {
    const name = params.name
    const year = params.year
    if(name.includes("conf")){
        return loadConference(name, year)
    }else if(name.includes("journals")){
        return loadJournal(name, year)
    }
}

async function loadConference(name: string, year: string){
    const data = await fetchBackend("conferences/"+name+"/"+year+"/proceedings");
    const proceedings = parseSparqlResult(data);
    const inproceedingsData = await fetchBackend("conferences/"+name+"/"+year+"/inproceedings");
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

async function loadJournal(name:string, year:string){
    const data = parseSparqlResult(await fetchBackend("journals/"+name+"/"+year))
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