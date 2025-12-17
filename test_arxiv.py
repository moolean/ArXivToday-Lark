import arxiv

client = arxiv.Client(page_size=200, delay_seconds=3)
search = arxiv.Search(
    query="cat:cs.CV",
    max_results=10,
    sort_by=arxiv.SortCriterion.SubmittedDate,
    sort_order=arxiv.SortOrder.Descending
)
papers = list(client.results(search))
for  i in papers:
    print(i.published.date().isoformat())