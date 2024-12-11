import base64

# 获取 sha1_hex_string 的方式：
# GooglePlay Console -> 设置 -> 应用完整性 -> 应用签名 -> SHA-1 证书指纹
sha1_hex_string = "4C:A4:2C:BA:3E:9D:F4..."
sha1_bytes = bytes.fromhex(sha1_hex_string.replace(":", ""))
facebook_hash = base64.b64encode(sha1_bytes).decode("utf-8")
print(facebook_hash)