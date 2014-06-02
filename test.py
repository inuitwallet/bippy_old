import encrypt.bip38 as bip38

intermediate = bip38.intermediate('thisisatest')
print('intermediate key = ' + intermediate)

BIPKey, address = bip38.intermediate2privK(intermediate)
print('BIP Key = ' + BIPKey)
print('address = ' + address)