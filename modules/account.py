import asyncio
import random
import time

from web3 import Web3
from web3.eth import AsyncEth
from web3.exceptions import TransactionNotFound
from hexbytes import HexBytes
from eth_account import Account as EthereumAccount
from loguru import logger
from settings.settings import SLEEP_FROM, SLEEP_TO

from utils.config import CHAINS_DATA, ERC_20_ABI
from utils.constansts import Status


class Account:
    def __init__(self, private_key: str, chain: str) -> None:
        self.private_key = private_key  
        self.chain = chain
        self.explorer = CHAINS_DATA["layerzero"]["explorer"]
        
        self.web3 = Web3(
            Web3.AsyncHTTPProvider(random.choice(CHAINS_DATA[chain]["rpc"])),
            modules={"eth": (AsyncEth, )})
        self.account = EthereumAccount.from_key(private_key)
        self.address = self.account.address
        
        self.logger = logger  
        
    def log_message(self, status: str, message: str):
        #{self.wallet_name:4}| 
        self.logger.log(status, f"{self.address} | {message}")
    
    def get_contract(self, contract_address: str, abi=None):
        contract_address = Web3.to_checksum_address(contract_address)
        
        if abi is None:
            abi = ERC_20_ABI
            
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        
        return contract

    def get_balance(self, contract_address: str) -> dict:
        contract = self.get_contract(contract_address)
        
        symbol = contract.functions.symbol().call()
        decimal = contract.functions.decimal().call()
        balance_wei = contract.functions.balance_wei().call()
        
        balance = balance_wei / 10 ** decimal
        
        return {
            "balance_wei": balance_wei,
            "balance": balance,
            "decimal": decimal,
            "symbol": symbol
        }
    
    async def wait_until_tx_finished(self, message: str, tx_hash: HexBytes, max_wait_time=180):
        start_time = time.time()
        
        while True:
            try:
                receipts = await self.web3.eth.get_transaction_receipt(tx_hash)
                status = receipts.get("status")
                
                if status == 1:
                    self.log_message(Status.SUCCESS, f"{message} - {self.explorer}{tx_hash.hex()}")
                    return True
                elif status is None:
                    await asyncio.sleep(1)
                else:
                    self.log_message(Status.ERROR, f"{self.explorer}{tx_hash.hex()}")
                    return False
            except TransactionNotFound:
                if time.time() - start_time > max_wait_time:
                    self.log_message(Status.FAILED, f"Tx: {self.explorer}{tx_hash.hex()}")
                    return False
                await asyncio.sleep(1)
    
    async def sign_tx(self, transaction):
        signed_tx = self.web3.eth.account.sign_transaction(transaction, self.private_key)
        
        return signed_tx
    
    async def sign_message(self, message):     
        signature = self.web3.eth.account.sign_message(message, private_key=self.private_key)
        
        return signature
    
    async def send_raw_transaction(self, signed_tx):
        txn_hash = await self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return txn_hash