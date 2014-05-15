import system.key as key
import math
import hashlib

def sxor(s1, s2):
	""" XOR strings
	"""
	return ''.join(chr(ord(a) ^ ord(b)) for a, b in zip(s1, s2))

__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
__b58base = len(__b58chars)


def b58encode(v):
  """ encode v, which is a string of bytes, to base58.    
  """

  long_value = 0L
  for (i, c) in enumerate(v[::-1]):
    long_value += ord(c) << (8*i) # 2x speedup vs. exponentiation

  result = ''
  while long_value >= __b58base:
    div, mod = divmod(long_value, __b58base)
    result = __b58chars[mod] + result
    long_value = div
  result = __b58chars[long_value] + result

  # Bitcoin does a little leading-zero-compression:
  # leading 0-bytes in the input become leading-1s
  nPad = 0
  for c in v:
    if c == '\0': nPad += 1
    else: break

  return (__b58chars[0]*nPad) + result


def b58decode(v, length=None):
  """ decode v into a string of len bytes
  """
  long_value = 0L
  for (i, c) in enumerate(v[::-1]):
    long_value += __b58chars.find(c) * (__b58base**i)

  result = ''
  while long_value >= 256:
    div, mod = divmod(long_value, 256)
    result = chr(mod) + result
    long_value = div
  result = chr(long_value) + result

  nPad = 0
  for c in v:
    if c == __b58chars[0]: nPad += 1
    else: break

  result = chr(0)*nPad + result
  if length is not None and len(result) != length:
    return None

  return result
	
	
def get_code_string(base):
	if base == 10:
		return "0123456789"
	elif base == 16:
		return "0123456789abcdef"
	elif base == 58:
		return "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
	elif base == 256:
		return ''.join([chr(x) for x in range(256)])
	else:
		raise ValueError("Invalid base!")


def encode(val, base, minlen=0):
	code_string = get_code_string(base)
	result = ""
	val = int(val)
	while val > 0:
		result = code_string[val % base] + result
		val /= base
	if len(result) < minlen:
		result = code_string[0] * (int(minlen) - len(result)) + result
	return result


def decode(string, base):
	code_string = get_code_string(base)
	result = 0
	if base == 16:
		string = string.lower()
	while len(string) > 0:
		result *= base
		result += code_string.find(string[0])
		string = string[1:]
	return result

	
def privKeyVersion(privK, cur):
	"""
		determine what sort of private key we have
		convert it to raw (base 10) and return

		from bitaddress:

		>> base58 decode input
		var bytes = Bitcoin.Base58.decode(privStr);
		>> set hash to be the first 34 characters of the bytes string array
		var hash = bytes.slice(0, 34);
		>>
		var checksum = Crypto.SHA256(Crypto.SHA256(hash, { asBytes: true }), { asBytes: true });
		if (checksum[0] != bytes[34] ||
					checksum[1] != bytes[35] ||
					checksum[2] != bytes[36] ||
					checksum[3] != bytes[37]) {
			throw "Checksum validation failed!";
		}
		var version = hash.shift();
		if (version != ECKey.privateKeyPrefix) {
			throw "Version " + version + " not supported!";
		}
		hash.pop();
		return hash;

		BigInteger.fromByteArrayUnsigned = function (ba) {
		if (!ba.length) {
			return ba.valueOf(0);
		} else if (ba[0] & 0x80) {
			// Prepend a zero so the BigInteger class doesn't mistake this
			// for a negative integer.
			return new BigInteger([0].concat(ba));
		} else {
			return new BigInteger(ba);
		}
	};

	"""
	if key.isWif(privK, cur):
		bytes = b58decode(privK)
		byteshash = bytes[:34]
		checksum = hashlib.sha256(hashlib.sha256(byteshash).digest()).digest()
		if checksum[0] != bytes[34] or	checksum[1] != bytes[35] or checksum[2] != bytes[36] or checksum[3] != bytes[37]:
			print('bad checksum')
			return False
		privK = decode(str(encode(int(decode(byteshash[:-1], 256)), 16)[2:]), 16)
	elif key.isHex(privK):
		privK = decode(privK, 16)
	elif key.isB64(privK):
		privK = privK.decode('base64', 'strict')
	elif key.isB6(privK):
		privK = privK.decode('base6', 'strict')
	return privK
		
