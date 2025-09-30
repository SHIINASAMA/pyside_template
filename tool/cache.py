import json
import logging
import os


def load_cache():
    """load cache from .cache/assets.json"""
    cache = {}
    if not os.path.exists('.cache'):
        os.makedirs('.cache')
    if os.path.exists('.cache/assets.json'):
        logging.info('Cache found.')
        with open('.cache/assets.json', 'r') as f:
            cache = json.load(f)
    if not cache:
        logging.info('No cache found.')
    return cache


def save_cache(cache):
    # save cache
    with open('.cache/assets.json', 'w') as f:
        json.dump(cache, f, indent=4)
    logging.info('Cache saved.')