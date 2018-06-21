import ads as ads
import progressbar

import json

with open('api.conf') as api_f:
    ads.config.token = api_f.read().strip()

SEARCH_DEPTH = 3
STARTING_QUERY = 'Lintott, C'

CACHED_PAPERS = {}
REMAINING_API_CALLS = 0

#def extend_authors(authors, seen_papers, papers):
#    new_authors = set()
#    for paper, paper_authors in papers.values():
#        if paper in seen_papers:
#            continue
#        seen_papers.add(paper)
#        for author in paper_authors:
#            if author not in authors:
#                new_authors.add(author)
#                authors[author] = set()
#            coauthors = authors[author]
#            for coauthor in paper.author:
#                if author == coauthor:
#                    continue
#                coauthors.add(coauthor)
#    return new_authors

def extend_authors(authors, seen_papers, papers):
    for paper, paper_authors in papers.items():
        if paper in seen_papers:
            continue
        seen_papers.add(paper)
        for author in paper_authors:
            authors[author] = (
                authors.get(author, set()) | set(paper_authors) - set(author)
            )

def cached_query(q):
    global CACHED_PAPERS
    global REMAINING_API_CALLS

    if not CACHED_PAPERS:
        with open('/opt/cache/cache.json') as cache_f:
            CACHED_PAPERS = json.load(cache_f)

    if q not in CACHED_PAPERS:
        results = ads.SearchQuery(author=q)
        CACHED_PAPERS[q] = {}
        for paper in results:
            if not paper.author:
                continue
            CACHED_PAPERS[q][paper.bibcode] = paper.author

        REMAINING_API_CALLS = results.response.get_ratelimits()['remaining']

    return CACHED_PAPERS[q]

try:
    authors = {}
    seen_papers = set()

    print("Getting initial authors")

    starting_papers = cached_query(q=STARTING_QUERY)
    extend_authors(authors, seen_papers, starting_papers)
    new_authors = set(authors.keys())
    previous_authors = new_authors

    for i in range(1, SEARCH_DEPTH - 1):
        print("Getting coauthors (iteration {})".format(i))
        for author in progressbar.progressbar(new_authors, redirect_stdout=True):
            q = cached_query(q=author)
            extend_authors(authors, seen_papers, q)

        print("Remaining ADS API calls: {}".format(REMAINING_API_CALLS))

        with open('/opt/cache/cache.json', 'w') as cache_f:
            json.dump(CACHED_PAPERS, cache_f)

        all_authors = set(authors.keys())
        new_authors = all_authors - previous_authors
        previous_authors = all_authors
finally:
    print("Remaining ADS API calls: {}".format(REMAINING_API_CALLS))
    with open('/opt/cache/cache.json', 'w') as cache_f:
        json.dump(CACHED_PAPERS, cache_f)
