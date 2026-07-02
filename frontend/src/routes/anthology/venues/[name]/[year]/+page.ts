import { fetchBackend } from '$lib/sparql/fetch.js'
import { parseSparqlResult, getIDFromURI } from '$lib/helperFunctions.js';

export async function entries() {
    const [conferences, journals, workshops] = await Promise.all([
        fetchBackend("conferences"),
        fetchBackend("journals"),
        fetchBackend("workshops")
    ]);
    const result: { name: string; year: string }[] = [];
    const seen = new Set<string>();

    for (const row of [...parseSparqlResult(conferences), ...parseSparqlResult(journals)]) {
        if (row.stream && row.year) {
            const name = getIDFromURI(row.stream);
            const key = `${name}/${row.year}`;
            if (!seen.has(key)) { seen.add(key); result.push({ name, year: row.year }); }
        }
    }
    for (const row of parseSparqlResult(workshops)) {
        if (row.year) {
            const key = `workshops/${row.year}`;
            if (!seen.has(key)) { seen.add(key); result.push({ name: 'workshops', year: row.year }); }
        }
    }
    return result;
}

export async function load({params}) {
    const name = params.name
    const year = params.year
    if (name === "workshops"){
        return loadWorkshops(year)
    }else if(name.includes("conf")){
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
        const volume = entry.volume ?? "-1";
        const issue = entry.number ?? "0"; 
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

async function loadWorkshops(year: string){
    const data = await fetchBackend("workshops/"+year+"/proceedings");
    const proceedings = parseSparqlResult(data);
    const inproceedingsData = await fetchBackend("workshops/"+year+"/inproceedings");
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