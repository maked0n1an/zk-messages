from modules import *



async def send_message(private_key, proxy):
    '''
    Send message
    ___________________________________________
    chain - from chain: polygon
    to_chain - to chain: arbitrum_nova, core, celo
    '''    
    
    chain               = 'polygon'
    to_chain            = 'arbitrum_nova'        
    
    zkMessenger = ZkMessenger(private_key, chain, proxy)
    await zkMessenger.send_message(to_chain)
    
    
async def send_message_to_random_chain(private_key, proxy):
    '''
    Send message using random chain
    ___________________________________________
    chain - from chain: polygon
    to_chain - to chain: arbitrum_nova, core, celo
    '''    
    
    chain               = 'polygon'
    random_chains       = ['arbitrum_nova', 'core', 'celo']
    
    zkMessenger = ZkMessenger(private_key,chain, proxy)
    await zkMessenger.send_message(random_chains) 
    