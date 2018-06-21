import ads as ads
import pandas
import progressbar

import json
import sys

with open('api.conf') as api_f:
    ads.config.token = api_f.read().strip()

SEARCH_DEPTH = 3
STARTING_QUERY = 'Lintott, C'

CACHED_PAPERS = {}
REMAINING_API_CALLS = 0

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
    seen_papers = set()

    print("Getting direct coauthors")

    starting_papers = cached_query(q=STARTING_QUERY)

    all_coauthors = set()
    for paper, authors in starting_papers.items():
        all_coauthors = all_coauthors | set(authors)

    print("Getting second order authors")

    all_2nd_order_coauthors = set()
    for author in progressbar.progressbar(all_coauthors):
        coauthor_papers = cached_query(author)
        for coauthor_paper, new_authors in coauthor_papers.items():
            all_2nd_order_coauthors = all_2nd_order_coauthors | set(new_authors)

    init_values = [False for x in all_2nd_order_coauthors]

    authors = pandas.DataFrame(
        {a:init_values for a in all_coauthors},
        index=all_2nd_order_coauthors,
    )

    print("Finding connections")
    for author in progressbar.progressbar(all_coauthors):
        coauthor_papers = cached_query(author)
        for coauthor_paper, second_order_authors in coauthor_papers.items():
            for second_order_author in second_order_authors:
                authors[author][second_order_author] = True
finally:
    print("Remaining ADS API calls: {}".format(REMAINING_API_CALLS))
    with open('/opt/cache/cache.json', 'w') as cache_f:
        json.dump(CACHED_PAPERS, cache_f)
