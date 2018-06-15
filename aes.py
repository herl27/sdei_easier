from Crypto.Cipher import AES
import base64

class AESECB:
    block_size = 16
    @staticmethod
    def encrypt(content,tk):
        byte_content = content.encode('utf-8')
        byte_key = tk.encode('utf-8')[0:16]
        aes_new = AES.new(byte_key,AES.MODE_ECB)
        if AESECB.block_size > len(byte_content):
            padding = AESECB.block_size - len(byte_content)
            byte_content = byte_content + chr(padding).encode('utf-8')*padding
        elif AESECB.block_size < len(byte_content):
            padding = AESECB.block_size - (len(byte_content)%AESECB.block_size)
            byte_content = byte_content + chr(padding).encode('utf-8') * padding
        else:
            byte_content = byte_content + chr(16).encode('utf-8') * 16
        result = aes_new.encrypt(byte_content)
        base_result = base64.b64encode(result).decode('utf-8').replace('\n','').replace('\r','')
        return base_result
