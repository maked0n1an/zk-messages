import asyncio
import random
import time
import aiohttp
from eth_typing import HexStr

from fake_useragent import UserAgent
from hexbytes import HexBytes
from utils.config import CHAINS_DATA, LZ_DATA, MESSENGER_ABI
from utils.constansts import Status
from utils.logger import setup_logger_for_wallet

from . import Account


class ZkMessenger(Account):
    def __init__(self, wallet_name: str, private_key: str, chain: str, to_chain: str, proxy=None):
        super().__init__(private_key, chain)
        self.wallet_name = wallet_name
        self.to_chain = random.choice(to_chain) if type(to_chain) == list else to_chain
        self.proxy = proxy or None
        self.scan = CHAINS_DATA[self.chain]['scan']
        self.logger = setup_logger_for_wallet(self.wallet_name)
        
    async def validate(self):
        ua = UserAgent()
        ua = ua.random
        headers = {
            'authority': 'api.zkbridge.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
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
            'public_key': self.address.lower(),
        }
        
        while True:
            
            url = 'https://api.zkbridge.com/api/signin/validation_message'
            
            try:               
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=url, json=json_data, 
                        headers=headers, proxy=self.proxy) as response:
                        
                        if response.status == 200:
                            message_header = await self._get_json(header='message', response=response)
                            signature = self.sign_message(message_header)
                            hex_signature = self.web3.to_hex(signature.signature)
                            
                            return headers, hex_signature
                        else:
                            self.log_message(Status.FAILED, f"Failed to validate: {response.status}")
            except aiohttp.ClientError as e:
                self.log_message(Status.ERROR, f"Error during HTTP request to identificate: {e}")
                await asyncio.sleep(5)
                            
    async def sign_in(self):
        headers, hex_signature = await self.validate()

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
                            token_header = await self._get_json(header='token', response=response)
                            headers['authorization'] = f"Bearer {token_header}"
                            
                            return headers
                        else:
                            self.log_message(Status.FAILED, f"Failed to sign: {response.status}")
            except aiohttp.ClientError as e:
                self.log_message(Status.ERROR, f"Error during HTTP request to sign: {e}")
                await asyncio.sleep(5)
                            
    async def profile(self):
        headers = await self.sign_in()
        
        url = 'https://api.zkbridge.com/api/user/profile'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, headers=headers, 
                        proxy=self.proxy) as response:
                    if response.status == 200:
                        self.log_message(Status.SUCCESS, f"{self.chain} | Successfully authorized")
                        
                        return headers
                    else:
                        self.log_message(Status.FAILED, f"Failed to authorize: {response.status}")
        except Exception as e:
            self.log_message(Status.ERROR, f"Error during HTTP request to authorize: {e}")
            await asyncio.sleep(5)
    
    async def _msg(self, 
        headers: dict[str],
        messenger_contract: str, 
        msg: str, 
        from_chain_id: int, 
        to_chain_id: int, 
        tx_hash: HexBytes
    ):
        timestamp = time.time()
        
        json_data = {
            "message": msg,
            "mailSenderAddress": messenger_contract,
            "receiverAddress": self.address,
            "receiverChainId": to_chain_id,
            "receiverDomainName": "",
            "sendTimestamp": timestamp,
            "senderAddress": self.address,
            "senderChainId": from_chain_id,
            "senderTxHash": tx_hash,
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
        n = random.randint(1, 20)
        string = []
        resource = "https://www.mit.edu/~ecprice/wordlist.10000"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(resource) as response:
                    if response.status == 200:
                        for i in range(n):
                            response = (await response.text()).split()
                            words = [g for g in response]
                            
                            string.append(random.choice(words))
                        message = ' '.join(string)
                        
                        return message
        except Exception as e:
            await asyncio.sleep(1)
            return await self._create_msg()
        
    async def send_message(self):
        data = await self.profile()
        
        if data:
            headers = data
        else:
            return 'error'
        
        contract = LZ_DATA["zkMessengerContracts"][self.chain]
        messenger_contract = self.get_contract(contract_address=contract, abi=MESSENGER_ABI)
        # lz_receiver_id = LZ_DATA['stargateChainIds'][self.to_chain] 
        receiver_chain_id = LZ_DATA['lzChainIds'][self.to_chain]
        sender_chain_id = LZ_DATA['lzChainIds'][self.chain]
        
        message = await self._create_msg()        
        dst_address = self.account.address
        _adapterParams = '0x00010000000000000000000000000000000000000000000000000000000000055730'
            
        while True:
            try: 
                self.log_message(Status.INFO, f"{self.chain} - is beginning to send to {self.to_chain} via L0...")
               
                tx_data = self.get_tx_data()
                
                tx = await messenger_contract.functions.sendMessage(
                    receiver_chain_id,
                    dst_address,
                    message,
                    _adapterParams
                ).build_transaction(tx_data)
                
                signed_txn = self.sign_tx(tx)
                
                bool_action = await self.wait_until_tx_finished("Successfully sent!", signed_txn)
                
                if bool_action:
                    msg = await self._msg(
                        headers, 
                        messenger_contract, 
                        message, 
                        sender_chain_id, 
                        receiver_chain_id,
                        signed_txn
                    )
                    if msg:
                        await self.wait_for_delay()
                        
                        return True
                else:
                    self.log_message(Status.RETRY, f'| {self.chain} - trying one more to send message...')
                    await self.send_message()
            except Exception as e:
                self.log_message(Status.ERROR, f"{self.chain} | Error while message sending: {e}")
                
    async def _get_json(self, header: str, response: aiohttp.ClientSession) -> str:
        try:
            message = await response.json()
            message = message[header]
            
            return message
        except Exception as e:
            self.log_message(Status.ERROR, f"Error while processing JSON response: {e}")
            
            return str(e)