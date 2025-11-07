"""
Utility Functions
"""

import os
import yaml
import requests
import json

def load_config():
    yaml_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(yaml_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def validate_llm_server_config(config: dict) -> dict:
    """
    Validate the configuration of LLM Server
    """
    fields = ['model', 'base_url', 'api_key']
    for field in fields:
        if field not in config:
            raise ValueError('Missing field `{}` in the configuration'.format(field))
    llm_server_config = {
        'model': config['model'],
        'base_url': config['base_url'],
        'api_key': config['api_key']
    }
    if not llm_server_config['api_key']:
        llm_server_config['api_key'] = 'ollama'  # Default for ollama service (any non-empty string)
    return llm_server_config


def get_llm_response(prompt: str, config: dict):
    """
    Get LLM response
    :param prompt: user prompt
    :param config: LLM Server configuration, fields include `model`, `base_url`, `api_key` etc.
    :return: the response content or None if failed
    """
    llm_server_config = validate_llm_server_config(config)
    model = llm_server_config['model']
    base_url = llm_server_config['base_url']
    api_key = llm_server_config['api_key']

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'stream': False
    }

    try:
        response = requests.post(
            base_url,
            headers=headers,
            data=json.dumps(data),
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print('LLM Server Error: {}'.format(e))
        return None


if __name__ == '__main__':
    config = load_config()
    print(config)
