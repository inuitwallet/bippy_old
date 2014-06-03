import encrypt.bip38 as bip38

intermediate = bip38.intermediate('thisisatest')
print('Intermediate Key = ' + intermediate)

BIPKey, address, confirmationcode = bip38.intermediate2privK(intermediate)
print('BIP Key = ' + BIPKey)
print('Address = ' + address)
print('Confirmation Code = ' + confirmationcode)

#output = bip38.confirmcode(confirmationcode, 'thisisatest')