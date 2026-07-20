# Shared body for the per-entity table templates below. It binds every label
# variable that build_filters may reference (?publication_label, ?venue_label,
# ?author_label, ?year_label) and performs the workshop -> synthetic venue collapse.
_ENTITY_TABLE_BODY = '''
  ?publication_URI dblp:title ?publication_label ;
                   dblp:yearOfPublication ?pubYear ;
                   dblp:authoredBy ?author_URI ;
                   dblp:publishedInStream ?stream_URI .

  OPTIONAL { ?publication_URI ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)
  BIND(STR(?year) AS ?year_label)

  OPTIONAL { ?stream_URI a ex:Workshop . BIND(true AS ?isWorkshop) }
  ?stream_URI dblp:primaryStreamTitle ?stream_label .
  BIND(IF(BOUND(?isWorkshop), <https://dblp.org/workshops>, ?stream_URI) AS ?venue_URI)
  BIND(IF(BOUND(?isWorkshop), "Workshops", ?stream_label) AS ?venue_label)
  OPTIONAL { ?author_URI dblp:primaryCreatorName ?author_label . }

  $FILTERS
'''

_ENTITY_TABLE_PREFIXES = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX ex: <https://ir.webis.de/kg#>
'''

AUTHOR_TABLE_TEMPLATE = f'''
{_ENTITY_TABLE_PREFIXES}
SELECT (?author_label AS ?Entity)
  (?author_URI AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
  (COUNT(DISTINCT ?venue_label)       AS ?Venues)
WHERE {{
{_ENTITY_TABLE_BODY}
}}
GROUP BY ?author_label ?author_URI
HAVING (BOUND(?author_label))
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
'''

VENUE_TABLE_TEMPLATE = f'''
{_ENTITY_TABLE_PREFIXES}
SELECT (?venue_label AS ?Entity)
  (?venue_URI AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
  (COUNT(DISTINCT ?author_label)      AS ?Authors)
  (STRAFTER(STR(?venue_rdf_type), "#") AS ?VenueType)
WHERE {{
{_ENTITY_TABLE_BODY}
  # sort key mirroring the frontend's venueDisplayLabel: the venue's abbreviation
  # (last parenthesized group of the title, else the uppercased URI tail) — the
  # Entity column displays abbreviations, so Entity sorting must order by them
  BIND(UCASE(IF(REGEX(?venue_label, "\\\\(([^)]+)\\\\)"),
                REPLACE(?venue_label, "^.*\\\\(([^)]+)\\\\).*$", "$1"),
                REPLACE(STR(?venue_URI), "^.*/", ""))) AS ?venue_sort)
  OPTIONAL {{
    ?venue_URI a ?venue_rdf_type .
    VALUES ?venue_rdf_type {{ dblp:Conference dblp:Journal }}
  }}
}}
GROUP BY ?venue_label ?venue_URI ?venue_sort ?venue_rdf_type
HAVING (BOUND(?venue_label))
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
'''

YEARS_TABLE_TEMPLATE = f'''
{_ENTITY_TABLE_PREFIXES}
SELECT (?year AS ?Entity)
  (?year AS ?URI)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
  (COUNT(DISTINCT ?venue_label)       AS ?Venues)
  (COUNT(DISTINCT ?author_label)      AS ?Authors)
WHERE {{
{_ENTITY_TABLE_BODY}
}}
GROUP BY ?year
$ORDER
LIMIT $LIMIT
OFFSET $OFFSET
'''

AUTHOR_YEAR_COUNTS_TEMPLATE = f'''
{_ENTITY_TABLE_PREFIXES}
SELECT (?author_URI AS ?URI) (GROUP_CONCAT(CONCAT(STR(?year), "@@", STR(?cnt)); separator=", ") AS ?Years)
WHERE {{
  SELECT ?author_URI ?year (COUNT(DISTINCT ?publication_URI) AS ?cnt)
  WHERE {{
    $SEED
{_ENTITY_TABLE_BODY}
  }}
  GROUP BY ?author_URI ?year
}}
GROUP BY ?author_URI
'''

PUBLICATION_TABLE_TEMPLATE = f'''
{_ENTITY_TABLE_PREFIXES}
SELECT ?Entity ?URI ?Authors ?authors ?authorIds ?Year
  (STRBEFORE(STRAFTER(?venuePair, "@@"), "@@") AS ?Venue)
  (STRAFTER(STRAFTER(?venuePair, "@@"), "@@") AS ?VenueURI)
WHERE {{
  SELECT (?publication_label AS ?Entity)
    (?publication_URI AS ?URI)
    (COUNT(DISTINCT ?author_label) AS ?Authors)
    (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
    (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
    (MIN(STR(?year)) AS ?Year)
    (MIN(CONCAT(?venue_sort, "@@", ?venue_label, "@@", STR(?venue_URI))) AS ?venuePair)
  WHERE {{
{_ENTITY_TABLE_BODY}
    # abbreviation-first pair: MIN picks (and sort_by=Venue orders by) the venue
    # abbreviation, matching what the Venue column displays
    BIND(UCASE(IF(REGEX(?venue_label, "\\\\(([^)]+)\\\\)"),
                  REPLACE(?venue_label, "^.*\\\\(([^)]+)\\\\).*$", "$1"),
                  REPLACE(STR(?venue_URI), "^.*/", ""))) AS ?venue_sort)
    # venue attribution (as in PERSON_TEMPLATE): keep non-workshop stream rows;
    # workshop rows only survive when the publication has no non-workshop stream
    FILTER(
      NOT EXISTS {{ ?stream_URI a ex:Workshop }}
      ||
      NOT EXISTS {{
        ?publication_URI dblp:publishedInStream ?s2 .
        FILTER NOT EXISTS {{ ?s2 a ex:Workshop }}
      }}
    )
    OPTIONAL {{
      ?publication_URI dblp:hasSignature ?sig .
      ?sig a dblp:AuthorSignature ;
           dblp:signatureOrdinal ?ord ;
           dblp:signatureCreator ?authorUri ;
           dblp:signatureDblpName ?authorName .
    }}
  }}
  GROUP BY ?publication_label ?publication_URI
  $ORDER
  LIMIT $LIMIT
  OFFSET $OFFSET
}}
$ORDER
'''

VENUE_YEAR_COUNTS_TEMPLATE = f'''
{_ENTITY_TABLE_PREFIXES}
SELECT (?venue_URI AS ?URI) (GROUP_CONCAT(CONCAT(STR(?year), "@@", STR(?cnt)); separator=", ") AS ?Years)
WHERE {{
  SELECT ?venue_URI ?year (COUNT(DISTINCT ?publication_URI) AS ?cnt)
  WHERE {{
    $SEED
{_ENTITY_TABLE_BODY}
  }}
  GROUP BY ?venue_URI ?year
}}
GROUP BY ?venue_URI
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

VENUE_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?year ?title ?streamTitle ?pub ?type ?proc WHERE {
  VALUES ?stream {
    <$VENUE_URI>
  }
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType ?type .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  ?stream dblp:primaryStreamTitle ?streamTitle .
  OPTIONAL {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:bibtexType bibtex:Proceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub ?type ?proc
ORDER BY ?type DESC(?year) ?title
'''

WORKSHOPS_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?year ?title ?streamTitle ?pub ?type ?proc WHERE {
  VALUES ?streamTitle {'Workshops'}
  ?stream a ex:Workshop .
  ?pub dblp:yearOfPublication ?pubYear ;
       dblp:publishedInStream ?stream ;
       dblp:title ?title ;
       dblp:bibtexType ?type .

  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  OPTIONAL {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:bibtexType bibtex:Proceedings .
  }
}
GROUP BY ?year ?title ?streamTitle ?pub ?type ?proc
ORDER BY ?type DESC(?year) ?title
'''

WORKSHOPS_YEAR_PROCEEDINGS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub ?streamTitle WHERE{
  ?stream a ex:Workshop .
  VALUES ?streamTitle {'Workshops'}
  ?pub dblp:title ?title ;
       dblp:publishedInStream ?stream ;
	   dblp:bibtexType bibtex:Proceedings ;
	   dblp:yearOfPublication ?pubYear .
       
  OPTIONAL { ?pub ex:yearOfConference ?eventYear }
  BIND(COALESCE(?eventYear, ?pubYear) AS ?year)

  FILTER(STR(?year) = "$YEAR")

  OPTIONAL{?pub dblp:doi ?doi_raw}
}
GROUP BY ?title ?pub ?streamTitle
'''

VENUE_YEAR_PROCEEDINGS_QUERY_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub ?streamTitle WHERE{
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

  OPTIONAL{?pub dblp:doi ?doi_raw}
}
GROUP BY ?title ?pub ?streamTitle
'''

INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?book ?pub
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

  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?book ?pub
'''

WORKSHOPS_INPROCEEDINGS_FROM_PROCEEDINGS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?book ?pub
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

  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?book ?pub
'''

CONFERENCE_LOOSE_PAPERS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub ?streamTitle
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  VALUES ?stream { <$VENUE_ID> }
  ?stream dblp:primaryStreamTitle ?streamTitle .
  ?pub dblp:publishedInStream ?stream ;
       dblp:yearOfPublication ?year ;
       dblp:title ?title .

  FILTER(STR(?year) = "$YEAR")
  FILTER NOT EXISTS { ?pub dblp:bibtexType bibtex:Proceedings }
  FILTER NOT EXISTS {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:publishedInStream ?stream .
  }

  OPTIONAL { ?pub dblp:doi ?doi_raw }
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?pub ?streamTitle
ORDER BY ?title
'''

WORKSHOPS_LOOSE_PAPERS_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title (MIN(STR(?doi_raw)) AS ?doi) ?pub
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", ?authorName); separator=", ") AS ?authors)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?ord), "@@", STR(?authorUri)); separator=", ") AS ?authorIds)
WHERE {
  ?stream a ex:Workshop .
  ?pub dblp:publishedInStream ?stream ;
       dblp:yearOfPublication ?year ;
       dblp:title ?title .

  FILTER(STR(?year) = "$YEAR")
  FILTER NOT EXISTS { ?pub dblp:bibtexType bibtex:Proceedings }
  FILTER NOT EXISTS {
    ?pub dblp:publishedAsPartOf ?proc .
    ?proc dblp:publishedInStream ?stream .
  }

  OPTIONAL { ?pub dblp:doi ?doi_raw }
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?pub
ORDER BY ?title
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

SELECT ?title ?booktitle ?series ?pages ?publisher (MIN(STR(?doi_raw)) AS ?doi) ?url ?year ?book ?pub ?stream ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
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
  OPTIONAL{?pub dblp:doi ?doi_raw}
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
GROUP BY ?title ?booktitle ?series ?pages ?publisher ?url ?year ?book ?pub ?stream ?streamTitle ?month ?volume ?number ?isbn ?bibtexType
'''

JOURNAL_YEAR_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX bibtex: <http://purl.org/net/nknouf/ns/bibtex#>

SELECT ?title ?journalTitle ?volume ?number (MIN(STR(?doi_raw)) AS ?doi) ?pub
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
  OPTIONAL{?pub dblp:doi ?doi_raw}
  OPTIONAL {
    ?pub dblp:hasSignature ?sig .
    ?sig a dblp:AuthorSignature ;
         dblp:signatureOrdinal ?ord ;
         dblp:signatureCreator ?authorUri ;
         dblp:signatureDblpName ?authorName .
  }
}
GROUP BY ?title ?journalTitle ?volume ?number ?pub
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

PEOPLE_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
SELECT ?person ?name WHERE {
  ?person a dblp:Creator .
  ?person dblp:primaryCreatorName ?name .
}
'''

PERSON_TEMPLATE = '''
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX ex: <https://ir.webis.de/kg#>

SELECT ?title ?year (MIN(STR(?doi_raw)) AS ?doi) ?pub ?name ?book ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream
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

  OPTIONAL { ?pub dblp:doi ?doi_raw }
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
GROUP BY ?title ?year ?pub ?name ?booktitle ?streamTitle ?journalVolume ?journalNumber ?stream ?book
'''