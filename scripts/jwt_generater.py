import secrets

# 生成 32 字节的随机十六进制字符串
secret_key = secrets.token_hex(32)
print(secret_key)