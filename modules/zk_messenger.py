import random

from . import Account


class ZkMessenger(Account):
    def __init__(self, private_key: str, chain: str, to_chain: str, proxy=None):
        super().__init__(private_key, chain)
        
        self.to_chain = random.choice(to_chain) if type(to_chain) == list else to_chain
        self.proxy = proxy or None
        