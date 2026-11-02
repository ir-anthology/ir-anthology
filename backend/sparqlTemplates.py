import re
from dataclasses import dataclass

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
  (COUNT(DISTINCT ?author_label)      AS ?Authors)
  (COUNT(DISTINCT ?publication_label) AS ?Publications)
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

# ---------------------------------------------------------------------------
# Query construction
# ---------------------------------------------------------------------------

# Characters SPARQL's IRIREF grammar forbids inside <...> (RFC 3987 + the SPARQL spec):
# <>"{}|^`\ and all control characters/space (#x00-#x20). There's no escape sequence for
# these inside an IRIREF, so a ir_id containing one is rejected rather than substituted.
_IRI_FORBIDDEN_CHARS = frozenset('<>"{}|^`\\') | {chr(c) for c in range(0x21)}

def get_uri_from_id(ir_id: str) -> str:
    uri = "https://dblp.org/" + ir_id.replace("+", "/")
    if any(c in _IRI_FORBIDDEN_CHARS for c in uri):
        raise ValueError("Invalid identifier")
    return uri

WORKSHOPS_VENUE_URI = "https://dblp.org/workshops"


@dataclass(frozen=True)
class TableSpec:
    """Everything that distinguishes one entity table from another.
    """

    template: str
    allowed_sorts: frozenset[str]
    # Columns that sort by a different variable than they display.
    sort_aliases: dict[str, str] | None = None
    # Set together: the per-year count template merged in by main._merge_year_counts,
    # and the raw triple-pattern variable its $SEED must target (see build_year_seed).
    year_counts_template: str | None = None
    year_seed_var: str | None = None


TABLES: dict[str, TableSpec] = {
    "Author": TableSpec(
        template=AUTHOR_TABLE_TEMPLATE,
        allowed_sorts=frozenset({"Entity", "Publications", "Venues"}),
        year_counts_template=AUTHOR_YEAR_COUNTS_TEMPLATE,
        year_seed_var="?author_URI",
    ),
    "Venue": TableSpec(
        template=VENUE_TABLE_TEMPLATE,
        allowed_sorts=frozenset({"Entity", "Publications", "Authors"}),
        sort_aliases={"Entity": "venue_sort"},
        year_counts_template=VENUE_YEAR_COUNTS_TEMPLATE,
        year_seed_var="?stream_URI",
    ),
    "Year": TableSpec(
        template=YEARS_TABLE_TEMPLATE,
        allowed_sorts=frozenset({"Entity", "Publications", "Venues", "Authors"}),
    ),
    "Publication": TableSpec(
        template=PUBLICATION_TABLE_TEMPLATE,
        allowed_sorts=frozenset({"Entity", "Year", "Authors", "Venue"}),
        sort_aliases={"Venue": "venuePair"},
    ),
}

def build_year_seed(entity: str, bindings: list) -> str | None:
    """Build the $SEED clause for the *_YEAR_COUNTS templates from the URIs of one result page.

    The seed restricts the per-year aggregation to the entities on the current page.
    It must target a raw triple-pattern variable (TableSpec.year_seed_var) — a VALUES on
    the BIND-computed ?entity_URI is not pushed down by the SPARQL engine, which
    would force aggregation over all ~100k entities (seconds instead of ~0.2s).

    Venue is special: the "Workshops" row uses the synthetic WORKSHOPS_VENUE_URI,
    which matches no triple. It is expressed as a UNION branch matching all
    ex:Workshop streams instead; the query body then collapses those back onto the
    synthetic URI. Returns None if the page contains no seedable URIs.
    """
    uris = [b["URI"]["value"] for b in bindings if b.get("URI", {}).get("type") == "uri"]
    if len(uris) == 0:
        return None
    if entity == "Venue":
        streams = [u for u in uris if u != WORKSHOPS_VENUE_URI]
        clauses = []
        if streams:
            values = " ".join(f"<{u}>" for u in streams)
            clauses.append(f"{{ VALUES ?stream_URI {{ {values} }} }}")
        if WORKSHOPS_VENUE_URI in uris:
            clauses.append("{ ?stream_URI a ex:Workshop . }")
        return " UNION ".join(clauses)
    values = " ".join(f"<{u}>" for u in uris)
    return f"VALUES {TABLES[entity].year_seed_var} {{ {values} }}"

def parse_order(sort_by: str | None, order: str, allowed: set[str] | None = None, aliases: dict[str, str] | None = None) -> str:
    # The frontend always sends explicit sort params. This static fallback is only a
    # safety net for malformed or legacy requests: LIMIT/OFFSET paging without an
    # ORDER BY would be nondeterministic, and ?Entity exists in every table template.
    if sort_by is None or (allowed is not None and sort_by not in allowed):
        sort_by, order = "Entity", "ASC"

    # some columns sort by a different variable than they display (e.g. the venues
    # Entity column shows abbreviations and sorts by ?venue_sort)
    sort_var = (aliases or {}).get(sort_by, sort_by)
    direction = "ASC" if (order or '').upper() == 'ASC' else 'DESC'
    return f"ORDER BY {direction}(?{sort_var})"

def get_label_var(entity_type: str) -> str:
    return f"?{entity_type.lower()}_label"

# filter_<key> becomes part of a SPARQL variable name (?<key>_label) with no string
# delimiter around it, so it can't be escaped the way a value can — it's either a
# syntactically valid identifier or it's a SPARQL injection. Validate the shape
# (matches how every real column name in this codebase is spelled) rather than
# maintaining a static list of known entities, so new filterable columns need no
# change here. Note: passing this check only makes a key *safe* to use, not
# *meaningful* — filtering on a key with no matching bound variable in the query body
# just filters out every row (see _ENTITY_TABLE_BODY for which ?..._label vars exist).
_SAFE_FILTER_KEY = re.compile(r'^[A-Za-z][A-Za-z0-9]*$')

def sparql_str_escape(s: str) -> str:
    """Escape a string for use inside a SPARQL "..." literal. Shared with dblp_fetch."""
    return s.replace('\\', '\\\\').replace('"', '\\"')

def build_filters(search_params: dict[str, str]) -> str :
    filters: dict[str, list[str]] = {}
    for key in search_params:
        if not key.startswith('filter_'):
            continue
        value = search_params[key];
        if value is None:
            continue
        entity = key[len('filter_'):]
        if not _SAFE_FILTER_KEY.fullmatch(entity):
            continue
        filters[entity] = value.split(',')

    if len(filters) == 0:
        return ''

    filter_clauses: list[str] = []
    for key in filters:
        values = filters[key]
        if  len(values) == 0:
            continue;
        label_var = get_label_var(key)
        contains_clauses = []
        for v in values:
            contains_clauses.append(f'CONTAINS(LCASE({label_var}), LCASE("{sparql_str_escape(v.lower())}"))')
        contains_string = f"{contains_clauses[0]}"
        for i in range(1, len(contains_clauses)):
            contains_string +=  f" || {contains_clauses[i]}"
        filter_clauses.append(f"FILTER({contains_string})")

    filter_string = f"{filter_clauses[0]}"
    for i in range(1, len(filter_clauses)):
        filter_string += f"\n  {filter_clauses[i]}"
    return filter_string;


def compose_table_query(template: str, *, filters: str, order: str, limit: int, offset: int) -> str:
    """Substitute the four placeholders every *_TABLE_TEMPLATE carries.

    Kept here rather than inline in main.py's _run_table_page so the warm-up query
    generator composes queries the exact same way instead of keeping its own copy.
    """
    return (template
            .replace('$FILTERS', filters)
            .replace('$ORDER', order)
            .replace('$LIMIT', str(limit))
            .replace('$OFFSET', str(offset)))
