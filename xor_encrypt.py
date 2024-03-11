"""
XOR Encryption
"""

data = "{username: 'admin', password: 'admin'}"

key = 3

encrypted = ''.join(chr(ord(c) ^ key) for c in data)

print(encrypted)