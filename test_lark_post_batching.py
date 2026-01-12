"""
Test script for verifying the batching logic in lark_post.py
This script tests the batching without making actual API calls
"""

from unittest.mock import Mock, patch, call
import json

# Import the function to test
from lark_post import post_to_lark_webhook


def create_test_papers(count):
    """Create a list of test papers"""
    return [
        {
            'title': f'Title {i+1}',
            'id': f'{1000000000 + i}',
            'abstract': f'Abstract {i+1}',
            'url': f'https://arxiv.org/abs/{1000000000 + i}',
            'published': '2021-01-01',
            'zh_abstract': f'中文摘要 {i+1}' if i % 2 == 0 else None,
            'comment': f'Comment {i+1}' if i % 3 == 0 else ''
        }
        for i in range(count)
    ]


def test_batching_logic():
    """Test that papers are correctly batched"""
    config = {
        'webhook_url': 'https://test.example.com/webhook',
        'template_id': 'test_template',
        'template_version_name': '1.0.0'
    }
    
    # Test case 1: Less than 20 papers (should send 1 batch)
    print("Test 1: 15 papers (should send 1 batch)")
    papers = create_test_papers(15)
    with patch('lark_post.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'code': 0}
        
        post_to_lark_webhook('Test Tag', papers, config)
        
        assert mock_post.call_count == 1, f"Expected 1 call, got {mock_post.call_count}"
        
        # Check that all 15 papers are in the request
        call_args = mock_post.call_args[1]['data']
        data = json.loads(call_args)
        paper_list = data['card']['data']['template_variable']['paper_list']
        assert len(paper_list) == 15, f"Expected 15 papers in batch, got {len(paper_list)}"
        assert paper_list[0]['counter'] == 1, "First paper counter should be 1"
        assert paper_list[14]['counter'] == 15, "Last paper counter should be 15"
        print("✓ Test 1 passed\n")
    
    # Test case 2: Exactly 20 papers (should send 1 batch)
    print("Test 2: 20 papers (should send 1 batch)")
    papers = create_test_papers(20)
    with patch('lark_post.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'code': 0}
        
        post_to_lark_webhook('Test Tag', papers, config)
        
        assert mock_post.call_count == 1, f"Expected 1 call, got {mock_post.call_count}"
        
        call_args = mock_post.call_args[1]['data']
        data = json.loads(call_args)
        paper_list = data['card']['data']['template_variable']['paper_list']
        assert len(paper_list) == 20, f"Expected 20 papers in batch, got {len(paper_list)}"
        assert paper_list[0]['counter'] == 1, "First paper counter should be 1"
        assert paper_list[19]['counter'] == 20, "Last paper counter should be 20"
        print("✓ Test 2 passed\n")
    
    # Test case 3: 25 papers (should send 2 batches: 20 + 5)
    print("Test 3: 25 papers (should send 2 batches)")
    papers = create_test_papers(25)
    with patch('lark_post.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'code': 0}
        
        post_to_lark_webhook('Test Tag', papers, config)
        
        assert mock_post.call_count == 2, f"Expected 2 calls, got {mock_post.call_count}"
        
        # Check first batch (20 papers)
        call_args_1 = mock_post.call_args_list[0][1]['data']
        data_1 = json.loads(call_args_1)
        paper_list_1 = data_1['card']['data']['template_variable']['paper_list']
        assert len(paper_list_1) == 20, f"Expected 20 papers in first batch, got {len(paper_list_1)}"
        assert paper_list_1[0]['counter'] == 1, "First batch first paper counter should be 1"
        assert paper_list_1[19]['counter'] == 20, "First batch last paper counter should be 20"
        assert '第 1/2 批' in data_1['card']['data']['template_variable']['tag'], "First batch should have batch indicator"
        
        # Check second batch (5 papers)
        call_args_2 = mock_post.call_args_list[1][1]['data']
        data_2 = json.loads(call_args_2)
        paper_list_2 = data_2['card']['data']['template_variable']['paper_list']
        assert len(paper_list_2) == 5, f"Expected 5 papers in second batch, got {len(paper_list_2)}"
        assert paper_list_2[0]['counter'] == 21, "Second batch first paper counter should be 21"
        assert paper_list_2[4]['counter'] == 25, "Second batch last paper counter should be 25"
        assert '第 2/2 批' in data_2['card']['data']['template_variable']['tag'], "Second batch should have batch indicator"
        print("✓ Test 3 passed\n")
    
    # Test case 4: 50 papers (should send 3 batches: 20 + 20 + 10)
    print("Test 4: 50 papers (should send 3 batches)")
    papers = create_test_papers(50)
    with patch('lark_post.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'code': 0}
        
        post_to_lark_webhook('Test Tag', papers, config)
        
        assert mock_post.call_count == 3, f"Expected 3 calls, got {mock_post.call_count}"
        
        # Check third batch (10 papers)
        call_args_3 = mock_post.call_args_list[2][1]['data']
        data_3 = json.loads(call_args_3)
        paper_list_3 = data_3['card']['data']['template_variable']['paper_list']
        assert len(paper_list_3) == 10, f"Expected 10 papers in third batch, got {len(paper_list_3)}"
        assert paper_list_3[0]['counter'] == 41, "Third batch first paper counter should be 41"
        assert paper_list_3[9]['counter'] == 50, "Third batch last paper counter should be 50"
        assert '第 3/3 批' in data_3['card']['data']['template_variable']['tag'], "Third batch should have batch indicator"
        print("✓ Test 4 passed\n")
    
    # Test case 5: 0 papers (should not send any request)
    print("Test 5: 0 papers (should not send any request)")
    papers = create_test_papers(0)
    with patch('lark_post.requests.post') as mock_post:
        post_to_lark_webhook('Test Tag', papers, config)
        
        assert mock_post.call_count == 0, f"Expected 0 calls for empty list, got {mock_post.call_count}"
        print("✓ Test 5 passed\n")
    
    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


if __name__ == '__main__':
    test_batching_logic()
