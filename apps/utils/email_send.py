#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import Random
import re

from django.core.mail import send_mail

from users.models import EmailVerifyRecord
from django.conf import settings


# 生成随机字符串
def random_str(random_length=8):
    s = ''
    # 生成字符串的可选字符串
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    for i in range(random_length):
        s += chars[Random().randint(0, length)]
    return s


def verify_email_format(email):
    p = re.compile('^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
    if p.match(email):
        return True
    else:
        return False


# 发送注册邮件,发送之前先保存到数据库，到时候查询链接是否存在
def send_register_email(request_uri, email, send_type='register'):
    # 检查邮箱格式，格式不正确发送邮件返回False
    if not verify_email_format(email):
        return False

    # 实例化一个EmailVerifyRecord对象
    email_record = EmailVerifyRecord()

    # 如果是修改邮箱，则发送4为验证码
    if send_type == 'update_email':
        code = random_str(4)
    else:
        # 生成随机的code放入链接
        code = random_str(16)

    email_record.code = code
    email_record.email = email
    email_record.send_type = send_type

    email_record.save()

    # 定义邮件内容
    email_title = ''
    email_body = ''

    if send_type == 'register':
        email_title = '在线学习平台 注册激活链接'
        email_body = '请点击链接激活账号：{}active/{}'.format(request_uri, code)  # request_uri='http://127.0.0.1:8000/register/'

        # 使用Django内置函数完成邮件发送。四个参数：主题，邮件内容，从哪里发，接受者list
        send_status = send_mail(email_title, email_body, settings.EMAIL_FROM, [email])
        if send_status:
            return True
        else:
            return False

    elif send_type == 'forget':
        email_title = '在线学习平台 密码重置链接'
        email_body = '请点击链接重置密码：{}reset/{}'.format(request_uri, code)  # request_uri='http://127.0.0.1:8000/forgetpwd/'

        # 使用Django内置函数完成邮件发送。四个参数：主题，邮件内容，从哪里发，接受者list
        send_status = send_mail(email_title, email_body, settings.EMAIL_FROM, [email])
        if send_status:
            return True
        else:
            return False

    elif send_type == 'update_email':
        email_title = '在线学习平台 修改邮箱地址'
        email_body = '用户邮箱修改确认验证码：{} （区分大小写）'.format(code)

        # 使用Django内置函数完成邮件发送。四个参数：主题，邮件内容，从哪里发，接受者list
        send_status = send_mail(email_title, email_body, settings.EMAIL_FROM, [email])
        if send_status:
            return True
        else:
            return False
