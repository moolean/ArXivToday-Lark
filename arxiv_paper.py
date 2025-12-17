"""
Get arXiv papers
"""

import os
import json
import arxiv
from tqdm import tqdm
from llm import is_paper_match, translate_abstract
import re


def get_latest_papers(category, max_results=100):
    """
    Get the latest papers from arXiv
    :param category: the category of papers
    :param max_results: the maximum number of papers to get
    :return: a list of papers
    """
    client = arxiv.Client(page_size=200, delay_seconds=3)
    search_query = f'cat:{category}'
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    
    papers = []
    for result in client.results(search):
        # Remove the version number from the id
        paper_id = result.get_short_id()
        version_pos = paper_id.find('v')
        if version_pos != -1:
            paper_id = paper_id[:version_pos]

        paper = {
            'title': result.title,
            'id': paper_id,
            'abstract': result.summary.replace('\n', ' '),  # Remove line breaks
            'url': result.entry_id,
            'published': result.published.date().isoformat(),  # Get the date in ISO format
            'comment': result.comment
        }
        papers.append(paper)

    return papers


def deduplicate_papers_across_categories(papers):
    """
    Deduplicate papers across multiple categories
    :param papers: a list of papers
    :return: the deduplicated papers
    """
    # Deduplicate papers while maintaining the order
    # **Note**: Used in the case where multiple categories are involved
    papers_id = set()
    deduplicated_papers = []
    for paper in papers:
        if paper['id'] not in papers_id:
            papers_id.add(paper['id'])
            deduplicated_papers.append(paper)
    return deduplicated_papers


def filter_papers_by_keyword(papers, keyword_list):
    """
    Filter papers by keywords
    :param papers: a list of papers
    :param keyword_list: a list of keywords
    :return: a list of filtered papers
    """
    results = []

    # Below is a less efficient way to filter papers by keywords
    # keyword_list = [keyword.lower() for keyword in keyword_list]
    # for paper in papers:
    #     if any(keyword in paper['abstract'].lower() for keyword in keyword_list):
    #         results.append(paper)
    use_keyword_list = []
    unused_keyword_list = []
    for keyword in keyword_list:
        keyword = keyword.lower()
        if keyword.startswith('-'):
            unused_keyword_list.append(keyword[1:])
        else:
            use_keyword_list.append(keyword)

    for paper in papers:
        title_lower = paper['title'].lower()
        abstract_lower = paper['abstract'].lower()

        paper_text = title_lower + ' ' + abstract_lower
        # Check if any of the use_keywords (as continuous phrases) are in the abstract
        # Check if any of the use_keywords (as whole words) are in the abstract
        has_use_keyword = any(re.search(r'\b' + re.escape(keyword) + r'\b', paper_text, re.IGNORECASE) for keyword in use_keyword_list)
        # Check if any of the unused_keywords (as whole words) are in the abstract
        has_unused_keyword = any(re.search(r'\b' + re.escape(keyword) + r'\b', paper_text, re.IGNORECASE) for keyword in unused_keyword_list)
        
        if has_use_keyword and not has_unused_keyword:
            results.append(paper)
    return results


def filter_papers_using_llm(papers, paper_to_hunt, config: dict):
    """
    Filter papers using LLM
    :param papers: a list of papers
    :param paper_to_hunt: the prompt describing the paper to hunt for
    :param config: the configuration of LLM Server
    :return: a list of filtered papers
    """
    results = []
    for paper in papers:
        if is_paper_match(paper, paper_to_hunt, config):
            results.append(paper)
    return results


def deduplicate_papers(papers, file_path):
    """
    Deduplicate papers according to the previous records
    :param papers: a list of papers
    :param file_path: the file path of the previous records
    :return: the deduplicated papers
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content:
            content = json.loads(content)
            # Filter out the duplicated papers by id
            content_id = set(d['id'] for d in content)
            papers = [d for d in papers if d['id'] not in content_id]
    # if len(set(d['id'] for d in papers)) == len(papers):
    #     return papers
    return papers


def prepend_to_json_file(file_path, data):
    """
    Prepend data to a JSON file
    :param file_path: the file path
    :param data: the data to prepend
    """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content:
            content = json.loads(content)
        else:
            content = []
    else:
        content = []

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data + content, f, indent=4, ensure_ascii=False)


def translate_abstracts(papers: list, config: dict):
    """
    Translate the abstracts using the specified translation service
    :param papers: a list of papers
    :param config: the configuration of LLM Server
    :return: the translated papers
    """
    for paper in tqdm(papers, desc='Translating Abstracts'):
        abstract = paper["abstract"]
        zh_abstract = translate_abstract(abstract, config)
        paper["zh_abstract"] = None
        if zh_abstract:
            paper["zh_abstract"] = zh_abstract
    return papers


if __name__ == '__main__':
    papers = get_latest_papers('cs.CL', max_results=50)
    print(json.dumps(papers, indent=4))
    print()
    keyword_list = ['safety', 'security', 'adversarial', 'jailbreak', 'backdoor', 'hallucination', 'victim']
    results = filter_papers_by_keyword(papers, keyword_list)
    print(json.dumps(results, indent=4))
    print()
    results = deduplicate_papers(results, 'papers.json')
    print(json.dumps(results, indent=4))
    print()
    prepend_to_json_file('papers.json', results)
