from Crypto.Hash import RIPEMD160

def create_ripemd160_hash(data):
    h = RIPEMD160.new()
    h.update(data)
    return h.digest()
