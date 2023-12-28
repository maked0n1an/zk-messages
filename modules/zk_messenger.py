import asyncio
import random
import time
from typing import List
import aiohttp

from fake_useragent import UserAgent
from eth_account.messages import encode_defunct
from utils.config import LZ_DATA, MESSAGES, MESSENGER_ABI
from utils.constansts import Status
from utils.helpers import retry

from . import Account


class ZkMessenger(Account):
    def __init__(self, private_key: str, chain: str, proxy=None):
        super().__init__(private_key, chain)
        self.proxy = proxy or None
        
    async def _validate(self):
        ua = UserAgent()
        ua = ua.random
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://zkbridge.com',
            'referer': 'https://zkbridge.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': ua,
        }
        
        json_data = {
            'publicKey': self.address.lower(),
        }
        
        while True:
            
            url = 'https://api.zkbridge.com/api/signin/validation_message'
            
            try:               
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=url, json=json_data, 
                        headers=headers, proxy=self.proxy) as response:
                        
                        if response.status == 200:
                            message_header = await self._get_header(header='message', response=response)
                            msg = encode_defunct(text=message_header)
                            sign = await self.sign_message(msg)
                            hex_signature = self.web3.to_hex(sign.signature)
                            
                            return headers, hex_signature
                        else:
                            self.log_message(Status.FAILED, f"Failed to validate: {response.status}")
            except aiohttp.ClientError as e:
                self.log_message(Status.ERROR, f"Error during HTTP request to identificate: {e}")
                await asyncio.sleep(5)
                            
    async def _sign_in(self):
        headers, hex_signature = await self._validate()

        json_data = {
            'publicKey': self.address.lower(),
            'signedMessage': hex_signature
        }
        
        while True:
            url = 'https://api.zkbridge.com/api/signin'
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=url, json=json_data, 
                        headers=headers, proxy=self.proxy) as response:
                        
                        if response.status == 200:
                            token_header = await self._get_header(header='token', response=response)
                            headers['authorization'] = f"Bearer {token_header}"
                            
                            return headers
                        else:
                            self.log_message(Status.FAILED, f"Failed to sign: {response.status}")
            except aiohttp.ClientError as e:
                self.log_message(Status.ERROR, f"Error during HTTP request to sign: {e}")
                await asyncio.sleep(5)
                            
    async def _profile(self):
        headers = await self._sign_in()
        params = ""
        
        url = 'https://api.zkbridge.com/api/user/profile?'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, params=params,
                    headers=headers, proxy=self.proxy) as response:
                    if response.status == 200:
                        self.log_message(Status.INFO, f"{self.chain} | ✅ Successfully authorized")
                        
                        return headers
                    else:
                        self.log_message(Status.FAILED, f"Failed to authorize: {response.status}")
        except Exception as e:
            self.log_message(Status.ERROR, f"Error during HTTP request to authorize: {e}")
            await asyncio.sleep(5)
    
    async def _confirm_message(self, 
        headers,
        messenger_contract, 
        msg, 
        from_chain_id, 
        to_chain_id, 
        tx_hash
    ):
        timestamp = time.time()
        
        json_data = {
            "message": msg,
            "mailSenderAddress": str(messenger_contract),
            "receiverAddress": self.address,
            "receiverChainId": to_chain_id,
            "receiverDomainName": "",
            "sendTimestamp": timestamp,
            "senderAddress": self.address,
            "senderChainId": from_chain_id,
            "senderTxHash": str(tx_hash),
            "sequence": 0,
            "receiverDomainName": "",
            "isL0": True
        }
        
        url = 'https://api.zkbridge.com/api/msg'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, json=json_data,
                    headers=headers, proxy=self.proxy) as response:
                    
                    if response.status == 200:
                        self.log_message(Status.SUCCESS, f"{self.chain} | The message has been confirmed")
                        
                        return True
                    else:
                        self.log_message(Status.FAILED, f"{self.chain} | Error while confirming message: {response.status}")
        except Exception as e:
            self.log_message(Status.ERROR, f"{self.chain} | Error while creating message : {e}")
            return False
        
    async def _create_msg(self):
        return random.choice(MESSAGES)
        
    async def _get_tx_data(self, contract: any, to_chain_id: int, message: str, _adapterParams: str):
        nonce = await self.web3.eth.get_transaction_count(self.address)        
        maxFeePerGas = int(await self.web3.eth.gas_price)
        maxPriority = int(await self.web3.eth.max_priority_fee)  
        
        fee = await contract.functions.fees(to_chain_id).call()
        zkFee = await contract.functions.estimateFee(to_chain_id, self.address, message, _adapterParams).call()
        value = zkFee + fee
        
        gas_data = {
            "nonce": nonce,
            "from": self.address,
            "value": value
        }

        gas = await contract.functions.sendMessage(
            to_chain_id, 
            self.address, 
            message, 
            _adapterParams
        ).estimate_gas(gas_data)      
        
        tx_data = {
            "nonce": nonce,
            "from": self.address,
            "value": value,
            "gas": gas,
            "maxFeePerGas": maxFeePerGas,
            "maxPriorityFeePerGas": maxPriority
        }

        return tx_data
    
    @retry
    async def send_message(self, to_chain):
        data = await self._profile()
        
        if type(to_chain) == list:
            to_chain = random.choice(to_chain)
        
        if data:
            headers = data
        else:
            return 'error'
        
        contract = LZ_DATA["zkMessengerContracts"][self.chain]
        messenger_contract = self.get_contract(contract_address=contract, abi=MESSENGER_ABI)
        receiver_chain_id = LZ_DATA['lzChainIds'][to_chain]
        sender_chain_id = LZ_DATA['lzChainIds'][self.chain]
        
        message = await self._create_msg()        
        dst_address = self.account.address
        _adapterParams = '0x00010000000000000000000000000000000000000000000000000000000000055730'
            
        while True:
            try: 
                self.log_message(Status.INFO, f"{self.chain} | start sending to <{to_chain}> via L0...")
                
                tx_data = await self._get_tx_data(messenger_contract, receiver_chain_id, message, _adapterParams)
                
                tx = await messenger_contract.functions.sendMessage(
                    receiver_chain_id,
                    dst_address,
                    message,
                    _adapterParams
                ).build_transaction(tx_data)
                
                signed_txn = await self.sign_tx(tx)
                tx_hash = await self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                bool_action = await self.wait_until_tx_finished(f"{self.chain} | {self.chain} -> {to_chain}", tx_hash)
                
                if bool_action and await self._confirm_message(                    
                        headers, 
                        messenger_contract, 
                        message, 
                        sender_chain_id, 
                        receiver_chain_id,
                        signed_txn
                    ):                        
                        return True
                    
                return bool_action
            except Exception as e:
                self.log_message(Status.ERROR, f"{self.chain} | Error while message sending: {e}")
                
                return False
                
    async def _get_header(self, header: str, response: aiohttp.ClientSession):
        try:
            json_response = await response.json()
            header = json_response[header]
            
            return header
        except Exception as e:
            self.log_message(Status.ERROR, f"Error while processing JSON response: {e}")
            
            return str(e)