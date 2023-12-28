import asyncio
import json
import random

from pathlib import Path
from .logger import logger

from settings.settings import RETRY_COUNT, SLEEP_FROM, SLEEP_TO
from utils.constansts import Status


def read_txt(filepath: Path | str):
    with open(filepath, 'r') as file:
        return [row.strip() for row in file]
    
def read_json(filepath: Path | str):
    with open(filepath, 'r') as file:
        return json.load(file)
    
def format_output(message: str):
    print(f"{message:^80}")    
    
def retry(func):
    async def _wrapper(*args, **kwargs):
        retries = 0
        while retries < RETRY_COUNT:
            try:
                result = await func(*args, **kwargs)
                
                return result
            except Exception as e:
                logger.error(f"Error | {e}")
                await initial_delay(10, 60)
                retries += 1
        
    return _wrapper
    
async def initial_delay(sleep_from=SLEEP_FROM, sleep_to=SLEEP_TO):
    delay_secs = random.randint(sleep_from, sleep_to)
    logger.log(Status.DELAY, f"- waiting for {delay_secs} to start wallet activities")
    await asyncio.sleep(delay_secs)