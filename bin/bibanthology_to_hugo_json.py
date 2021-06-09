import json
import os
from pathlib import Path
import html

def iterate_over_events(basedir, outputdir, wcspdir):
    venue_index = VenueIndex()
    volume_index = VolumeIndex()
    paper_index = PaperIndex()
    people_index = PeopleIndex()
    for event_type in ["workshop", "conference", "journal"]:
        paths = map(str,Path(os.path.join(basedir, event_type)).rglob('*.jsonl'))
        for path in paths:
            year = None
            lines = []
            with open(path, "r") as file:
                for line in file:
                    line = json.loads(line)
                    lines.append(line)
                    this_year = int(line["fields"]["year"]) if "year" in line["fields"] else None
                    if year is None:
                        year = this_year
                    else: 
                        if this_year is None:
                            raise Exception("year is missing for paper "+line["bibid"])
                        year += this_year
            year = round(year/len(lines))
            year = str(year)
            generic_venue_id = get_venue_id(basedir, path)
            #same for conf and workshop
            venue_id =  generic_venue_id+"_"+event_type
            #must be different for workshop and conference
            #venue_id must be also in volume id
            #where volume_id := <year>.<venue_id>-<volume_name>
            event_id = str(year) + "." + venue_id
            volume_id = event_id + "-" + get_volume_name(path)
            venue_index.append(venue_id, (basedir, generic_venue_id), year, volume_id, event_type)
            #paper index must be served before the volume index
            paper_index.append(lines, year, volume_id, event_id, people_index, venue_id)
            volume_index.append(lines, venue_id, year, volume_id, paper_index, event_id)
    venue_index.dump(outputdir)
    volume_index.dump(outputdir)
    paper_index.dump(outputdir)
    people_index.dump(outputdir)
    paper_index.dump_wcsp(wcspdir, venue_index)
    with open(os.path.join(outputdir, "sigs.json"), "w") as file:
        file.write("{}")

def get_venue_id(basedir, path):
    path = path[len(basedir)+1:]
    path = path[path.find(os.sep)+1:]
    return path[:path.find(os.sep)]

def get_volume_name(path):
    name = os.path.basename(path)
    return name[:name.rfind(".")]

def get_base_venue(basedir, generic_venue_id):
    with open(os.path.join(basedir, "meta", generic_venue_id+".json"), "r") as file:
        temp = json.loads(file.read())["fields"]
        return {"is_toplevel":True, "name":temp["name"], "acronym":temp["acronym"]}


class PaperIndex:
    def __init__(self):
        self.index = {}

    def append(self, lines, year, volume_id, event_id, people_index, venue_id):
        if event_id not in self.index:
            self.index[event_id] = {}
        d = self.index[event_id]
        booktitle = extract_booktitle(lines, year)
        for i, paper in enumerate(lines):
            metacount = "prefix---@"+volume_id
            if metacount not in d:
                d[metacount] = 0
            paper_number = str(d[metacount])
            d[metacount] += 1
            paper_id = volume_id+"."+paper_number
            paper_dict = paper["fields"].copy()
            paper_dict.update({
                "bibkey":paper["bibid"],
                "bibtype":paper["entrytype"], 
                "booktitle":booktitle, 
                "booktitle_html":html.escape(booktitle),
                "paper_id":paper_number,
                "parent_volume_id":volume_id,
                "language":None,
                "title":paper["fields"]["title"],
                "title_html":html.escape(paper["fields"]["title"]),
                "year":paper["fields"]["year"],
            })
            if "url" in paper["fields"]:
                url = paper["fields"]["url"]
                if url.endswith(".pdf"):
                    paper_dict["pdf"] = url
                else: 
                    paper_dict["url"] = url
                    if url.startswith("https://doi.org/"):
                        paper_dict["doi"] = url[17:]
            if paper["bibid"].startswith("DBLP:"):
                paper_dict["dblp"] = paper["bibid"][5:]
            authors = []
            persons = Person.authors_of_paper(paper)
            for person in persons:
                people_index.append(person, persons, paper_id, venue_id)
                p = {"id":person.get_id(), "full":person.get_full(), "first":person.get_first(), "last":person.get_last()}
                orc = person.get_orc_id()
                dblp = person.get_dblp_id()
                if orc is not None:
                    p["orc"] = orc
                if dblp is not None:
                    p["dblp"] = dblp
                authors.append(p)
            paper_dict["author"] = authors
            paper_dict["author_string"] = paper["fields"]["author"].replace(" and ", ", ") if "author" in paper["fields"] else None
            editors = []
            persons = Person.editors_of_paper(paper)
            for person in persons:
                people_index.append(person, persons, paper_id, venue_id)
                p = {"id":person.get_id(), "full":person.get_full(), "first":person.get_first(), "last":person.get_last()}
                orc = person.get_orc_id()
                dblp = person.get_dblp_id()
                if orc is not None:
                    p["orc"] = orc
                if dblp is not None:
                    p["dblp"] = dblp
                editors.append(p)
            paper_dict["editor"] = editors
            paper_dict["editor_string"] = paper["fields"]["editor"].replace(" and ", ", ") if "editor" in paper["fields"] else None
            d[paper_id] = paper_dict
        
    def dump(self, outputdir):
        os.makedirs(os.path.join(outputdir, "papers"), exist_ok=True)
        for key, value in self.index.items():
            ks = list(value.keys())
            for key_inner in ks:
                if key_inner.startswith("prefix---@"):
                    del value[key_inner]
            with open(os.path.join(outputdir, "papers", key+".json"), "w") as file:
                file.write(json.dumps(value)) 
    
    def dump_wcsp(self, outputdir, venue_index):
        with open(os.path.join(outputdir, "wcsp.ldjson"), "w") as file:
            for key, value in self.index.items():
                for key_inner, value_inner in value.items():
                    if key_inner.startswith("prefix---@"):
                        continue
                    value_inner = value_inner.copy()
                    value_inner["anthologyId"] = key_inner
                    if "author" in value_inner:
                        value_inner["authors"] = value_inner["author"]
                        del value_inner["author"]
                        del value_inner["author_string"]
                    if "editor" in value_inner:
                        value_inner["editors"] = value_inner["editor"]
                        del value_inner["editor"]
                        del value_inner["editor_string"]
                    venue_id = key.split(".")[1]
                    value_inner["venue"] = venue_index.index[venue_id]["acronym"]
                    print(json.dumps(value_inner), file=file) 

class Person:
    def authors_of_paper(paper):
        if "author" in paper["fields"]:
            names = paper["fields"]["author"].split(" and ")
            authors = list(filter(lambda x: x["role"]=="author", paper["fields"]["personids"]))
            persons = list(map(lambda x: Person(*x), zip(names, authors)))
            return persons
        return []

    def editors_of_paper(paper):
        if "editor" in paper["fields"]:
            names = paper["fields"]["editor"].split(" and ")
            editors = list(filter(lambda x: x["role"]=="editor", paper["fields"]["personids"]))
            persons = list(map(lambda x: Person(*x), zip(names, editors)))
            return persons
        return []

    def __init__(self, name, meta):
        s = name.split(" ")
        self.first = " ".join(s[:-1])
        self.last = s[-1]
        self.dblp_id = meta["dblpid"]
        self.id = self.dblp_id.lower().replace(" ", "+")
        self.orc_id = meta["orcid"] if "orcid" in meta else None

    def get_id(self):
        return self.id
    
    def get_first(self):
        return self.first

    def get_last(self):
        return self.last

    def get_full(self):
        return self.first + " " + self.last

    def get_orc_id(self):
        return self.orc_id

    def get_dblp_id(self):
        return self.dblp_id
    



class VenueIndex:
    def __init__(self):
        self.index = {}

    def append(self, venue_id, get_base_venue_args, year, volume_id, event_type):
        if venue_id in self.index:
            d = self.index[venue_id]
        else:
            d = get_base_venue(*get_base_venue_args)
            d = VenueIndex.setType(d, event_type)
            d["slug"] = venue_id
            d["volumes_by_year"] = {}
            d["years"] = []
        if year not in d["years"]:
            d["years"].append(year)
        if year not in d["volumes_by_year"]:
            d["volumes_by_year"][year] = []
        d["volumes_by_year"][year].append(volume_id)
        self.index[venue_id] = d
        
    def setType(d, event_type):
        if "is_conf" in d:
            return d
        if event_type == "conference":
            d["is_conf"] = True
            d["is_journal"] = False
            d["is_workshop"] = False
            return d
        if event_type == "journal":
            d["is_conf"] = False
            d["is_journal"] = True
            d["is_workshop"] = False
            return d
        if event_type == "workshop":
            d["is_conf"] = False
            d["is_journal"] = False
            d["is_workshop"] = True
            return d
        raise Exception("unkown type")
        
    def dump(self, outputdir):
        os.makedirs(outputdir, exist_ok=True)
        with open(os.path.join(outputdir, "venues.json"), "w") as file:
            file.write(json.dumps(self.index)) 

class VolumeIndex:
    def __init__(self):
        self.index = {}

    def append(self, lines, venue_id, year, volume_id, paper_index, event_id):
        d = {}
        d["has_abstracts"] = False
        d["meta_date"] = year
        d["year"] = year
        d["sigs"] = []
        d["venues"] = [venue_id]
        d["papers"] = []
        if lines[0]["entrytype"] == "proceedings":
            proceeding = paper_index.index[event_id][volume_id+".0"]
            d_keys = list(d.keys())
            for key, value in proceeding.items():
                if key in d_keys:
                    continue
                d[key] = value
        for i in range(0, len(lines)):
            d["papers"].append(volume_id+"."+str(i))
        if "title" not in d:
            d["title"] = extract_booktitle(lines, year)
            d["title_html"] = extract_booktitle(lines, year)
        self.index[volume_id] = d
        
    def dump(self, outputdir):
        os.makedirs(outputdir, exist_ok=True)
        with open(os.path.join(outputdir, "volumes.json"), "w") as file:
            file.write(json.dumps(self.index)) 

class PeopleIndex:
    def __init__(self):
        self.index = {}

    def append(self, person, persons, paper_id, venue_id):
        persons = set(persons)
        p_id = person.get_id()
        if p_id[0] not in self.index:
            self.index[p_id[0]] = {}
        if p_id not in self.index[p_id[0]]:
            d = {"first":person.get_first(), "last":person.get_last(), "full":person.get_full(), "slug":p_id, "venues":[], "coauthors":[], "papers":[]}
            self.index[p_id[0]][p_id] = d
        d = self.index[p_id[0]][p_id]
        done = False
        for venue in d["venues"]:
            if venue[0] == venue_id:
                venue[1] += 1
                done = True
                break
        if not done:
            d["venues"].append([venue_id, 1])
        for coaut_true in persons:
            done = False
            coaut_id = coaut_true.get_id()
            for coaut_check in d["coauthors"]:
                if coaut_check[0] == coaut_id:
                    coaut_check[1] += 1
                    done = True
                    break
            if not done:
                d["coauthors"].append([coaut_id, 1])
        d["papers"].append(paper_id)
        
    def dump(self, outputdir):
        os.makedirs(os.path.join(outputdir, "people"), exist_ok=True)
        for key, value in self.index.items():
            with open(os.path.join(outputdir, "people", key+".json"), "w") as file:
                file.write(json.dumps(value)) 

        


def extract_booktitle(lines, year):
    if lines[0]["entrytype"] == "proceedings" and "title" in  lines[0]["fields"]:
        return lines[0]["fields"]["title"]
    else: 
        if "booktitle" in lines[0]["fields"]:
            return lines[0]["fields"]["booktitle"]
        else:
            title = str(year)
            if "volume" in lines[0]["fields"]:
                title += " Volume " + lines[0]["fields"]["volume"]
            if "number" in lines[0]["fields"]:
                title += " Issue " + lines[0]["fields"]["number"]
            return title


iterate_over_events("data/final", "build/data", ".")