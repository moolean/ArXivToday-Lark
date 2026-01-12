"""
HTTP POST request to Lark Webhook API
"""

import json
import datetime
import requests


def post_to_lark_webhook(tag: str, papers: list, config: dict):
    headers = {
        'Content-Type': 'application/json'
    }

    # Split papers into batches of maximum 20
    batch_size = 20
    total_papers = len(papers)
    
    if total_papers == 0:
        print("No papers to send")
        return
    
    # Calculate number of batches needed
    num_batches = (total_papers + batch_size - 1) // batch_size
    
    print(f"Total papers: {total_papers}, splitting into {num_batches} batch(es)")
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_papers)
        batch_papers = papers[start_idx:end_idx]
        
        print(f"Sending batch {batch_num + 1}/{num_batches} with {len(batch_papers)} papers (papers {start_idx + 1}-{end_idx})")
        
        # Card Template Data
        today_date = datetime.date.today().strftime('%Y-%m-%d')
        table_rows = [
            {
                "index": start_idx + i + 1,
                "title": paper['title'],
                "id": paper['id'],
                "published": paper['published'],
                "url": f"[{paper['url']}]({paper['url']})"
            }
            for i, paper in enumerate(batch_papers)
        ]
        paper_list = [
            {
                "counter": start_idx + i + 1,
                "title": paper['title'],
                "id": paper['id'],
                "abstract": paper['zh_abstract'] if paper.get('zh_abstract', None) else paper.get('abstract', None),
                # "zh_abstract": paper.get('zh_abstract', None),
                "url": paper['url'],
                "published": paper['published'],
                "comment": paper['comment'] if paper['comment'] else ""
            }
            for i, paper in enumerate(batch_papers)
        ]
        
        # Add batch info to tag if there are multiple batches
        batch_tag = tag if num_batches == 1 else f"{tag} (第 {batch_num + 1}/{num_batches} 批)"

        card_data = {
            "type": "template",
            "data": {
                "template_id": config['template_id'],
                "template_version_name": config['template_version_name'],
                "template_variable": {
                    "today_date": today_date,
                    "tag": batch_tag,
                    "total_paper": total_papers,
                    # "table_rows": table_rows,
                    "paper_list": paper_list
                }
            }
        }

        data = {
            "msg_type": "interactive",
            "card": card_data
        }
       
        # Send HTTP POST request
        response = requests.post(config['webhook_url'], headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            print(f"Batch {batch_num + 1}/{num_batches} sent successfully")
            print(f"Response:\n{response.json()}")
        else:
            print(f"Batch {batch_num + 1}/{num_batches} failed, status code: {response.status_code}")
            print(f"Response:\n{response.text}")


if __name__ == '__main__':
    papers = [
        {
            'title': 'Title 1',
            'id': '1234567890',
            'abstract': 'Abstract 1',
            'url': 'https://arxiv.org/abs/1234567890',
            'published': '2021-01-01',
            'zh_abstract': None
        },
        {
            'title': 'Title 2',
            'id': '2345678901',
            'abstract': 'Abstract 2',
            'url': 'https://arxiv.org/abs/2345678901',
            'published': '2021-01-02',
            'zh_abstract': '中文摘要 2'
        }
    ]
    from utils import load_config
    config = load_config()
    post_to_lark_webhook('test', papers, config)
