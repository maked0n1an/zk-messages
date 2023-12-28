from utils.helpers import read_json, read_txt

PRIVATE_KEYS = read_txt("input_data/private_keys.txt")

PROXIES = read_txt("input_data/proxies.txt")

# WALLET_NAMES = read_txt("input_data/wallet_names.txt")

MESSAGES = read_txt("data/messages/messages.txt")

CHAINS_DATA = read_json("data/chains/chains.json")

LZ_DATA = read_json('data/chains/lz_data.json')

ERC_20_ABI = read_json("data/abi/erc_20_abi.json")

MESSENGER_ABI = read_json('data/abi/zk_messenger.json')