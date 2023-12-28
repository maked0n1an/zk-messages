import asyncio
import random
import sys
from loguru import logger

import questionary
from questionary import Choice

from settings.modules_settings import *
from settings.settings import IS_SHUFFLE_WALLETS, IS_SLEEP, SLEEP_FROM, SLEEP_TO
from utils.config import PRIVATE_KEYS, PROXIES
from utils.helpers import initial_delay, format_output
from utils.logger import setup_logger_for_output

def greetings():
    brand_label = "========== M A K E D 0 N 1 A N =========="
    name_label = "========= zkMessenger (via zkBridge) ========="
    
    print("")
    format_output(brand_label)
    format_output(name_label)

def is_bot_setuped_to_start():
    end_bot = True

    if len(PRIVATE_KEYS) == 0:
        logger.error("Don't imported private keys in 'private_keys.txt'!")
        return
    if len(PROXIES) == 0:
        logger.error("Don't imported proxies in 'proxies.txt'!")
        return
    # if len() == 0:
    #     logger.error("Please insert names into wallet_names.txt")
    #     return
    # if len(PRIVATE_KEYS) != len(WALLET_NAMES):
    #     logger.error("The wallet names' amount must be equal to private keys' amount")
    #     return

    return end_bot

def get_module():
    result = questionary.select(
        "Select a method to get started",
        choices=[
            Choice("1) Send message", send_message),
            Choice("2) Send message to random chain", send_message_to_random_chain),
            Choice("3) Exit", "exit"),
        ],
        qmark="⚙️ ",
        pointer="✅ "
    ).ask()
    if result == "exit":
        exit_label = "========= It's all! ========="
        format_output(exit_label)
        sys.exit()
    return result

def get_wallets():
    wallets = [
        {
            "key": key,
            "proxy": proxy,
        } for key, proxy in zip(PRIVATE_KEYS, PROXIES * len(PRIVATE_KEYS))
    ]

    return wallets

async def run_module(module, wallet):
    return await module(wallet["key"], wallet["proxy"])

async def main(module):  
    wallets = get_wallets()

    if IS_SHUFFLE_WALLETS:
        random.shuffle(wallets)
    
    for wallet in wallets:
        is_result = await run_module(module, wallet)
        
        if IS_SLEEP and wallet != wallets[-1] and is_result:
            await initial_delay(SLEEP_FROM, SLEEP_TO)          
    
if __name__ == "__main__":
    greetings()    
    setup_logger_for_output()
    
    if is_bot_setuped_to_start():
        module = get_module()      
        
        asyncio.run(main(module))
    else:
        exit_label = "========= The bot has ended it's work! ========="
        format_output(exit_label)
        sys.exit() 