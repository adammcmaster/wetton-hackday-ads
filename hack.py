import ads as ads

with open('api.conf') as api_f:
    ads.config.token = api_f.read().strip()

SEARCH_DEPTH = 3
STARTING_QUERY = 'galaxy zoo'

def extend_authors(authors, seen_papers, papers):
    new_authors = set()
    for paper in papers:
        if paper.id in seen_papers:
            continue
        seen_papers.add(paper.id)
        if not paper.author:
            continue
        for author in paper.author:
            if author not in authors:
                new_authors.add(author)
                authors[author] = set()
            coauthors = authors[author]
            for coauthor in paper.author:
                if author == coauthor:
                    continue
                coauthors.add(coauthor)
    return new_authors

authors = {}
seen_papers = set()

starting_papers = ads.SearchQuery(q=STARTING_QUERY)
extend_authors(authors, seen_papers, starting_papers)
new_authors = authors.keys()
print(authors)

for i in range(SEARCH_DEPTH - 1):
    next_authors = set()
    for author in new_authors:
        next_authors = (
            next_authors
            | extend_authors(authors, seen_papers,
                             ads.SearchQuery(author=author)
                            )
        )
    new_authors = next_authors
    print("New authors: {}".format(new_authors))
    print(authors)
