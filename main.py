"""
Main Script
"""

import os
import datetime
from arxiv_paper import get_latest_papers, deduplicate_papers_across_categories, filter_papers_by_keyword, filter_papers_using_llm, deduplicate_papers, prepend_to_json_file, translate_abstracts
from lark_post import post_to_lark_webhook
from utils import load_config


# Load Configuration
config = load_config()
tag = config['tag']
category_list = config['category_list']
keyword_list = config['keyword_list']
use_llm_for_filtering = config['use_llm_for_filtering']
use_llm_for_translation = config['use_llm_for_translation']

paper_file = os.path.join(os.path.dirname(__file__), 'papers.json')
if use_llm_for_filtering:
    with open(os.path.join(os.path.dirname(__file__), 'paper_to_hunt.md'), 'r', encoding='utf-8') as f:
        paper_to_hunt = f.read()


def task():
    """
    Main task: Fetch Papers & Post to Lark Webhook
    """
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    print('Task: {}'.format(today_date))

    papers = []
    for category in category_list:
        papers.extend(get_latest_papers(category, max_results=90))
    print('Total papers: {}'.format(len(papers)))

    # Deduplicate papers across categories
    papers = deduplicate_papers_across_categories(papers)
    print('Deduplicated papers across categories: {}'.format(len(papers)))

    if keyword_list:
        papers = filter_papers_by_keyword(papers, keyword_list)
    print('Filtered papers by Keyword: {}'.format(len(papers)))

    if use_llm_for_filtering:
        papers = filter_papers_using_llm(papers, paper_to_hunt, config)
        print('Filtered papers by LLM: {}'.format(len(papers)))

    papers = deduplicate_papers(papers, paper_file)
    print('Deduplicated papers: {}'.format(len(papers)))

    if use_llm_for_translation:
        papers = translate_abstracts(papers, config)
        print('Translated Abstracts into Chinese')
    # print(papers)
    prepend_to_json_file(paper_file, papers)

    # Post to Lark Webhook
    post_to_lark_webhook(tag, papers, config)


if __name__ == '__main__':
    # Run the task immediately
    task()

    ### Uncomment the following code to use `schedule` to run the task periodically ###
    # import time
    # import schedule
    # # Schedule the task to run every day at 10:17
    # schedule.every().day.at("10:17").do(task)  # TODO: Change the time for your own need
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
