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
  (COUNT(DISTINCT ?year_label)        AS ?Year)
  (COUNT(DISTINCT ?2020s_label)       AS ?2020s)
  (COUNT(DISTINCT ?2010s_label)       AS ?2010s)
  (COUNT(DISTINCT ?2000s_label)       AS ?2000s)
  (COUNT(DISTINCT ?Pre2000s_label)    AS ?Pre2000s)
WHERE {
  VALUES ?entityType { "$ENTITY_TYPE" }
  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?year_label ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?venue_URI .

  OPTIONAL {
    ?venue_URI dblp:primaryStreamTitle ?venue_label .
  }
  OPTIONAL {
    ?author_URI dblp:primaryCreatorName ?author_label .
  }
  
  BIND(xsd:integer(STR(?year_label)) AS ?y)
  
  BIND(IF(?y >= 2020, STR(?year_label), ?unbound) AS ?2020s_label)
  BIND(?2020s_label AS ?2020s_URI)
  BIND(IF(?y >= 2010 && ?y < 2020, STR(?year_label), ?unbound) AS ?2010s_label)
  BIND(?2010s_label AS ?2010s_URI)
  BIND(IF(?y >= 2000 && ?y < 2010, STR(?year_label), ?unbound) AS ?2000s_label)
  BIND(?2000s_label AS ?2000s_URI)
  BIND(IF(?y < 2000, STR(?year_label), ?unbound) AS ?Pre2000s_label)
  BIND(?Pre2000s_label AS ?Pre2000s_URI)
  
  $FILTERS

  BIND(
    IF(?entityType = "Publication", ?publication_URI,
    IF(?entityType = "Venue",       ?venue_URI,
    IF(?entityType = "Year",        ?year_URI,
    IF(?entityType = "2020s",       ?2020s_URI,
    IF(?entityType = "2010s",       ?2010s_URI,
    IF(?entityType = "2000s",       ?2000s_URI,
    IF(?entityType = "Pre2000s",    ?Pre2000s_URI,
                                    ?author_URI)))))))
  AS ?entity_URI)
  BIND(
    IF(?entityType = "Publication", ?publication_label,
    IF(?entityType = "Venue",       ?venue_label,
    IF(?entityType = "Year",        ?year_label,
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

# With the new scheme we can also distinguish between journal and conference
ANTHOLOGY_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>

SELECT DISTINCT ?stream ?venue_label ?year_label ?type
WHERE {
  VALUES ?stream {
      <https://dblp.org/streams/journals/ftir>
      <https://dblp.org/streams/journals/ijirr>
      <https://dblp.org/streams/journals/ijmir>
      <https://dblp.org/streams/journals/ipm>
      <https://dblp.org/streams/journals/ir>
      <https://dblp.org/streams/journals/jasis>
      <https://dblp.org/streams/journals/sigir>
      <https://dblp.org/streams/journals/tismir>
      <https://dblp.org/streams/journals/tist>
      <https://dblp.org/streams/journals/tois>
      <https://dblp.org/streams/journals/tweb>
      <https://dblp.org/streams/journals/wwwj>
      <https://dblp.org/streams/conf/adcs>
      <https://dblp.org/streams/conf/airs>
      <https://dblp.org/streams/conf/ccir>
      <https://dblp.org/streams/conf/ceri>
      <https://dblp.org/streams/conf/chiir>
      <https://dblp.org/streams/conf/cikm>
      <https://dblp.org/streams/conf/civr>
      <https://dblp.org/streams/conf/clef>
      <https://dblp.org/streams/conf/coria>
      <https://dblp.org/streams/conf/desires>
      <https://dblp.org/streams/conf/dir>
      <https://dblp.org/streams/conf/ecir>
      <https://dblp.org/streams/conf/fdia>
      <https://dblp.org/streams/conf/fire>
      <https://dblp.org/streams/conf/ictir>
      <https://dblp.org/streams/conf/irfc>
      <https://dblp.org/streams/conf/ismir>
      <https://dblp.org/streams/conf/mir>
      <https://dblp.org/streams/conf/ntcir>
      <https://dblp.org/streams/conf/sigir>
      <https://dblp.org/streams/conf/spire>
      <https://dblp.org/streams/conf/trec>
      <https://dblp.org/streams/conf/wsdm>
      <https://dblp.org/streams/conf/www>
  }
  ?publication_URI dblp:yearOfPublication ?year_label ;
                   dblp:publishedInStream ?stream .

  ?stream a ?type ;
          dblp:primaryStreamTitle ?venue_label .
  FILTER(?type != dblp:Stream)
}
ORDER BY ?type ?venue_label ?year_label 
'''

YEARS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT DISTINCT ?year_label ?title ?streamTitle ?pub WHERE{
VALUES ?stream {
<$VENUE_URI>
}
?pub dblp:yearOfPublication ?year_label ;
                 dblp:publishedInStream ?stream ;
                 dblp:title ?title ;
                 dblp:bibtexType bibtex:Proceedings .
?stream dblp:primaryStreamTitle ?streamTitle .
}
'''
'''
const VENUE_PROCEEDINGS_TEMPLATE = `
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?year_label ?title ?streamTitle ?pub (COUNT(DISTINCT ?paper) AS ?count) WHERE {
  {
    SELECT DISTINCT ?stream WHERE{
      { BIND(<$VENUE_URI> AS ?stream) }
      UNION
      { ?stream dblp:superStream <$VENUE_URI> .}
      UNION
      { <$VENUE_URI> dblp:subStream ?stream .}
    }
  }
  ?pub dblp:yearOfPublication ?year_label ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType bibtex:Proceedings .
  <$VENUE_URI> dblp:primaryStreamTitle ?streamTitle .
  OPTIONAL {
    ?paper dblp:publishedAsPartOf ?pub ;
           dblp:bibtexType bibtex:Inproceedings .
  }
}
GROUP BY ?year_label ?title ?streamTitle ?pub
ORDER BY DESC(?year_label) ?title
'''

VENUE_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?year_label ?title ?streamTitle ?pub (COUNT(DISTINCT ?paper) AS ?count) WHERE {
  VALUES ?stream {
    <$VENUE_URI>
  }
  ?pub dblp:yearOfPublication ?year_label ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType bibtex:Proceedings .
  ?stream dblp:primaryStreamTitle ?streamTitle .
  OPTIONAL {
    ?paper dblp:publishedAsPartOf ?pub ;
           dblp:bibtexType bibtex:Inproceedings .
  }
}
GROUP BY ?year_label ?title ?streamTitle ?pub
ORDER BY DESC(?year_label) ?title
'''

PROCEEDINGS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?doi ?pub ?streamTitle WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?year .
  ?stream dblp:primaryStreamTitle ?streamTitle .
  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:doi ?doi}
}
GROUP BY ?title ?doi ?pub ?streamTitle
'''

INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?doi ?book ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE{
  VALUES ?stream {
    <$VENUE_ID>
  }
  ?book dblp:publishedInStream ?stream ;
        dblp:bibtexType bibtex:Proceedings ;
        dblp:yearOfPublication ?year .
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
	   dblp:yearOfPublication ?year .

  ?stream dblp:primaryStreamTitle ?streamTitle .

  OPTIONAL{?pub dblp:publishedInSeries ?series}
  OPTIONAL{?pub dblp:pagination ?pages}
  OPTIONAL{?pub dblp:doi ?doi}
  OPTIONAL{?pub dblp:publishedBy ?publisher}
  OPTIONAL{?pub dblp:primaryDocumentPage ?url}
  OPTIONAL{?pub dblp:monthOfPublication ?month}
  OPTIONAL{?pub dblp:publishedInJournalVolume ?volume}
  OPTIONAL{?pub dblp:publishedInJournalVolumeIssue ?number}
  OPTIONAL{?pub dblp:isbn ?isbn}
  OPTIONAL{?pub dblp:hasSignature ?sig .
            ?sig a dblp:AuthorSignature ;
                 dblp:signatureOrdinal ?ord ;
                 dblp:signatureCreator ?authorUri ;
                 dblp:signatureDblpName ?authorName}
  OPTIONAL {?pub dblp:publishedAsPartOf ?book .
            ?book dblp:title ?booktitle .
            OPTIONAL {
                ?book dblp:editedBy ?editor .
                ?editor dblp:primaryCreatorName ?editorName .
                OPTIONAL {
                    ?book dblp:hasSignature ?bookEdSig .
                    ?bookEdSig dblp:signatureCreator ?editor ;
                               dblp:signatureOrdinal ?edOrd .
                }
            }
            OPTIONAL { ?book dblp:publishedBy ?publisher }
            OPTIONAL { ?book dblp:publishedInSeries ?series }
  }

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
	   dblp:yearOfPublication ?year .
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

# Workaround for multiple stream titles is SAMPLE(...). Don't know if there is a better way
PERSON_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>

SELECT ?title ?year ?doi ?pub ?name ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  VALUES ?author {
    <$AUTHOR>
  }
  ?pub dblp:authoredBy ?author ;
       dblp:bibtexType ?bibtexType ;
       dblp:yearOfPublication ?year ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title .

  OPTIONAL { ?pub dblp:doi ?doi }
  OPTIONAL { ?author dblp:primaryCreatorName ?name }
  OPTIONAL { ?pub dblp:publishedAsPartOf ?book .
             ?book dblp:title ?booktitle }
  OPTIONAL { ?stream dblp:primaryStreamTitle ?streamTitle }
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