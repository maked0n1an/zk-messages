from utils.helpers import read_json


CHAINS_DATA = read_json("data/chains/chains.json")

LZ_DATA = read_json('data/chains/lz_data.json')

ERC_20_ABI = read_json("data/abi/erc_20_abi.json")

MESSENGER_ABI = read_json('data/abi/zk_messenger.json')