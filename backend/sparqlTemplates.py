TABLE_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

SELECT (?entity_label AS ?Entity)
  (?entity_URI AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publication)
  (COUNT(DISTINCT ?venue_label)       AS ?Venue)
  (COUNT(DISTINCT ?author_label)      AS ?Author)
  (COUNT(DISTINCT ?year)              AS ?Year)
  (COUNT(DISTINCT ?2020s_label)       AS ?2020s)
  (COUNT(DISTINCT ?2010s_label)       AS ?2010s)
  (COUNT(DISTINCT ?2000s_label)       AS ?2000s)
  (COUNT(DISTINCT ?Pre2000s_label)    AS ?Pre2000s)
WHERE {
  VALUES ?entityType { "$ENTITY_TYPE" }
  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?venue_URI .

  OPTIONAL { ?publication_URI dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  OPTIONAL {
    ?venue_URI dblp:primaryStreamTitle ?venue_label .
  }
  OPTIONAL {
    ?author_URI dblp:primaryCreatorName ?author_label .
  }
  
  BIND(xsd:integer(STR(?year)) AS ?y)
  
  BIND(IF(?y >= 2020, STR(?year), ?unbound) AS ?2020s_label)
  BIND(?2020s_label AS ?2020s_URI)
  BIND(IF(?y >= 2010 && ?y < 2020, STR(?year), ?unbound) AS ?2010s_label)
  BIND(?2010s_label AS ?2010s_URI)
  BIND(IF(?y >= 2000 && ?y < 2010, STR(?year), ?unbound) AS ?2000s_label)
  BIND(?2000s_label AS ?2000s_URI)
  BIND(IF(?y < 2000, STR(?year), ?unbound) AS ?Pre2000s_label)
  BIND(?Pre2000s_label AS ?Pre2000s_URI)
  
  $FILTERS

  BIND(
    IF(?entityType = "Publication", ?publication_URI,
    IF(?entityType = "Venue",       ?venue_URI,
    IF(?entityType = "Year",        ?year,
    IF(?entityType = "2020s",       ?2020s_URI,
    IF(?entityType = "2010s",       ?2010s_URI,
    IF(?entityType = "2000s",       ?2000s_URI,
    IF(?entityType = "Pre2000s",    ?Pre2000s_URI,
                                    ?author_URI)))))))
  AS ?entity_URI)
  BIND(
    IF(?entityType = "Publication", ?publication_label,
    IF(?entityType = "Venue",       ?venue_label,
    IF(?entityType = "Year",        ?year,
    IF(?entityType = "2020s",       ?2020s_label,
    IF(?entityType = "2010s",       ?2010s_label,
    IF(?entityType = "2000s",       ?2000s_label,
    IF(?entityType = "Pre2000s",    ?Pre2000s_label,
                                    ?author_label)))))))
  AS ?entity_label)

}
GROUP BY ?entity_label ?entity_URI
HAVING (BOUND(?entity_label) && BOUND(?entity_URI))
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
'''

ANTHOLOGY_CONFERENCES_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?stream ?venue_label ?year ?type
WHERE {
  VALUES ?type {dblp:Conference}
  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .

  FILTER NOT EXISTS { ?stream a ex:Workshop }

  ?pub ex:yearOfConference ?year ;
       dblp:publishedInStream ?stream .
}
ORDER BY ?type ?venue_label ?year
'''

ANTHOLOGY_WORKSHOPS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?stream ?venue_label ?year ?type
WHERE {
  VALUES ?type {ex:Workshop}
  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .

  ?pub ex:yearOfConference ?year ;
       dblp:publishedInStream ?stream .
}
ORDER BY ?type ?venue_label ?year
'''

ANTHOLOGY_JOURNALS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?stream ?venue_label ?year ?type
WHERE {
  VALUES ?type { dblp:Journal }
  ?pub dblp:yearOfPublication ?year ;
                   dblp:publishedInStream ?stream .

  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .
}
ORDER BY ?type ?venue_label ?year 
'''

YEARS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT DISTINCT ?year ?title ?streamTitle ?pub WHERE{
  VALUES ?stream {
  <$VENUE_URI>
  }
  ?pub dblp:yearOfPublication ?pubYear ;
      dblp:publishedInStream ?stream ;
      dblp:title ?title ;
      dblp:bibtexType bibtex:Proceedings .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
}
'''
'''
const VENUE_PROCEEDINGS_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?year ?title ?streamTitle ?pub (COUNT(DISTINCT ?paper) AS ?count) WHERE {
  {
    SELECT DISTINCT ?stream WHERE{
      { BIND(<$VENUE_URI> AS ?stream) }
      UNION
      { ?stream dblp:superStream <$VENUE_URI> .}
      UNION
      { <$VENUE_URI> dblp:subStream ?stream .}
    }
  }
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType bibtex:Proceedings .

  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  <$VENUE_URI> dblp:primaryStreamTitle ?streamTitle .
  OPTIONAL {
    ?paper dblp:publishedAsPartOf ?pub ;
           dblp:bibtexType bibtex:Inproceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub
ORDER BY DESC(?year) ?title
'''

VENUE_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?year ?title ?streamTitle ?pub (COUNT(DISTINCT ?paper) AS ?count) WHERE {
  VALUES ?stream {
    <$VENUE_URI>
  }
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType bibtex:Proceedings .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
  OPTIONAL {
    ?paper dblp:publishedAsPartOf ?pub ;
           dblp:bibtexType bibtex:Inproceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub
ORDER BY DESC(?year) ?title
'''

WORKSHOPS_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?year ?title ?streamTitle ?pub (COUNT(DISTINCT ?paper) AS ?count) WHERE {
  VALUES ?streamTitle {'Workshops'}
  ?stream a ex:Workshop .
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType bibtex:Proceedings .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  OPTIONAL {
    ?paper dblp:publishedAsPartOf ?pub ;
           dblp:bibtexType bibtex:Inproceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub
ORDER BY DESC(?year) ?title
'''

WORKSHOPS_YEAR_PROCEEDINGS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?doi ?pub ?streamTitle WHERE{
  ?stream a ex:Workshop .
  VALUES ?streamTitle {'Workshops'}
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:doi ?doi}
}
GROUP BY ?title ?doi ?pub ?streamTitle
'''

PROCEEDINGS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?doi ?pub ?streamTitle WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:doi ?doi}
}
GROUP BY ?title ?doi ?pub ?streamTitle
'''

INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?doi ?book ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?book dblp:publishedInStream ?stream ;
        dblp:bibtexType bibtex:Proceedings ;
        dblp:yearOfPublication ?pubYear .

  OPTIONAL { ?book ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  ?pub dblp:publishedAsPartOf ?book ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Inproceedings .

  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?doi ?book ?pub
'''

WORKSHOPS_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?doi ?book ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  ?stream a ex:Workshop .
  ?book dblp:publishedInStream ?stream ;
        dblp:bibtexType bibtex:Proceedings ;
        dblp:yearOfPublication ?pubYear .

  OPTIONAL { ?book ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  ?pub dblp:publishedAsPartOf ?book ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Inproceedings .

  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?doi ?book ?pub
'''

PUBLICATIONS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?pub ?title WHERE {
  ?pub a dblp:Publication .
  ?pub dblp:title ?title .
}
'''

BIB_PUBLICATION_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?booktitle ?series ?pages ?publisher ?doi ?url ?year ?book ?pub ?stream ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?edOrd), "@@", ?editorName); separator=", ") AS ?editors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?edOrd), "@@", STR(?editor)); separator=", ") AS ?editorIds)
WHERE{
  VALUES ?pub {
    <$PUBLICATION>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType ?bibtexType ;
	   dblp:yearOfPublication ?pubYear .

  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .

  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:publishedBy ?pubPublisher}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?pub dblp:monthOfPublication ?month}
  OPTIONAL{?pub dblp:publishedInJournalVolume ?journalVolume}
  OPTIONAL{?pub dblp:publishedInSeriesVolume ?seriesVolume}
  BIND(COALESCE(?journalVolume, ?seriesVolume) AS ?pubVolume)
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:publishedInSeries ?pubSeries }
  OPTIONAL{?pub dblp:isbn ?isbn}
  OPTIONAL{?pub dblp:hasSignature ?sig .
            ?sig a dblp:AuthorSignature ;
                 dblp:signatureOrdinal ?ord ;
                 dblp:signatureCreator ?authorUri ;
                 dblp:signatureDblpName ?authorName}
  OPTIONAL {
                ?pub dblp:editedBy ?pubEditor .
                ?pubEditor dblp:primaryCreatorName ?pubEditorName .
                OPTIONAL {
                    ?pub dblp:hasSignature ?pubEdSig .
                    ?pubEdSig dblp:signatureCreator ?pubEditor ;
                              dblp:signatureOrdinal ?pubEdOrd .
                }
            }
  OPTIONAL {?pub dblp:publishedAsPartOf ?book .
            ?book dblp:title ?booktitle .
            OPTIONAL {
                ?book dblp:editedBy ?bookEditor .
                ?bookEditor dblp:primaryCreatorName ?bookEditorName .
                OPTIONAL {
                    ?book dblp:hasSignature ?bookEdSig .
                    ?bookEdSig dblp:signatureCreator ?bookEditor ;
                               dblp:signatureOrdinal ?bookEdOrd .
                }
            }
            OPTIONAL { ?book dblp:publishedBy ?bookPublisher }
            OPTIONAL { ?book dblp:publishedInSeries ?bookSeries }
            OPTIONAL{?book dblp:publishedInSeriesVolume ?bookSeriesVolume}
  }
  BIND(COALESCE(?pubPublisher, ?bookPublisher) AS ?publisher)  
  BIND(COALESCE(?pubSeries, ?bookSeries) AS ?series)  
  BIND(COALESCE(?pubEditor, ?bookEditor) AS ?editor)
  BIND(COALESCE(?pubEditorName, ?bookEditorName) AS ?editorName)
  BIND(COALESCE(?pubEdOrd, ?bookEdOrd) AS ?edOrd)  
  BIND(COALESCE(?pubVolume, ?bookSeriesVolume) AS ?volume)

}
GROUP BY ?title ?booktitle ?series ?pages ?publisher ?doi ?url ?year ?book ?pub ?stream ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
'''

ARTICLES_FROM_JOURNAL_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?journalTitle ?volume ?number ?doi ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  VALUES ?journal {
    <$JOURNAL>
  }
  ?journal dblp:primaryStreamTitle ?journalTitle .
  ?pub dblp:publishedInStream ?journal ;
       dblp:title ?title ;
	   dblp:bibtexType bibtex:Article ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")
  OPTIONAL{?pub dblp:publishedInJournalVolume ?volume}
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?journalTitle ?volume ?number ?doi ?pub
'''

JOURNAL_OVERVIEW_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?year ?volume ?number ?journalTitle (COUNT(DISTINCT ?pub) AS ?count) WHERE {
  VALUES ?journal {
    <$JOURNAL>
  }
  ?journal dblp:primaryStreamTitle ?journalTitle .
  ?pub dblp:publishedInStream ?journal ;
       dblp:bibtexType bibtex:Article ;
       dblp:yearOfPublication ?year .

  OPTIONAL { ?pub dblp:publishedInJournalVolume ?volume }
  OPTIONAL { ?pub dblp:publishedInJournalVolumeIssue ?number }
}
GROUP BY ?year ?volume ?number ?journalTitle
ORDER BY DESC(?year) ?volume ?number
'''

PERSONS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?person ?name WHERE {
  ?person a dblp:Creator .
  ?person dblp:primaryCreatorName ?name .
}
'''

PERSON_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?year ?doi ?pub ?name ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  VALUES ?author {
    <$AUTHOR>
  }
  ?pub dblp:createdBy ?author ;
       dblp:bibtexType ?bibtexType ;
       dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title .

  ?stream dblp:primaryStreamTitle ?streamTitle .
  FILTER(
    NOT EXISTS { ?stream a ex:Workshop }
    ||
    NOT EXISTS {
      ?pub dblp:publishedInStream ?s2 .
      FILTER NOT EXISTS { ?s2 a ex:Workshop }
    }
  )

  OPTIONAL { ?pub dblp:yearOfEvent ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  OPTIONAL { ?pub dblp:doi ?doi }
  OPTIONAL { ?author dblp:primaryCreatorName ?name }
  OPTIONAL { ?pub dblp:publishedAsPartOf ?book .
             ?book dblp:title ?booktitle }
  OPTIONAL { ?pub dblp:publishedInJournalVolume ?journalVolume }
  OPTIONAL { ?pub dblp:publishedInJournalVolumeIssue ?journalNumber }
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?year ?doi ?pub ?name ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream
'''