# # -*-encoding:utf-8-*-
# # from simplecrypt import encrypt, decrypt

# # from flask import current_app
# from Crypto.Cipher import AES
# from binascii import hexlify, unhexlify

# # from mongoengine.fields import EmailField
# # from mongoengine.base import BaseField

# # cobj = AES.new(current_app.config['SECRET_KEY'], AES.MODE_CBC, current_app.config['SECRET_KEY'])

# __all__ = ['decrypt', 'encrypt']


# def encrypt(text):
#     pad_cnt = len(text) + 16 - (len(text) % 16)
#     return hexlify(cobj.encrypt(text.ljust(pad_cnt))).decode('utf8')


# def decrypt(text):
#     return cobj.decrypt(unhexlify(text)).decode('utf8').strip()


# # class EncryptedEmailField(EmailField):

# #     def to_python(self, value):
# #         original_value = value
# #         try:
# #             return decrypt(value)
# #         except:
# #             from flask import current_app
# #             current_app.logger.critical('failed to decrypt email')
# #             return original_value

# #     def to_mongo(self, value):
# #         # return super(EncryptedEmailField, self).to_mongo(encrypt(value))
# #         return encrypt(value)

# #     def prepare_query_value(self, op, value):
# #         return super(EncryptedEmailField, self).prepare_query_value(op, encrypt(value))
