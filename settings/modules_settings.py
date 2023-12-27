from modules import *

async def send_message(wallet_name, private_key, proxy):
    '''
    Send messege
    ___________________________________________
    chain - from chain
    to_chain - to chain
    '''
    
    chain = 'polygon'
    to_chain = 'core'    
    
    
    zkMessenger = ZkMessenger(wallet_name, private_key, chain, to_chain, proxy)
    zkMessenger.send_message()
    