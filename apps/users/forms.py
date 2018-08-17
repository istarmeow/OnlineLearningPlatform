#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
from django import forms

from captcha.fields import CaptchaField

from .models import UserProfile


class LoginForm(forms.Form):
    # 用户名和密码不能为空
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, min_length=5)


# 新注册用户表单
class RegisterForm(forms.Form):
    # 此处email与前端name需保持一致
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=5)
    # 应用验证码
    captcha = CaptchaField()  # 如果验证码错误提示是英文，可以在括号内加入 error_messages={'invalid': '验证码错误'}


# 忘记密码表单
class ForgetPwdForm(forms.Form):
    email = forms.EmailField(required=True)
    captcha = CaptchaField(error_messages={'invalid': '验证码错误'})


# 重置密码form实现
class ModifyPwdForm(forms.Form):
    # 密码不能小于5位
    password = forms.CharField(required=True, min_length=5)
    # 密码不能小于5位
    re_password = forms.CharField(required=True, min_length=5)


# 用户头像上传表单
class UserImageUploadForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('image', )

    @staticmethod
    def valid_image(image_name):
        """
        验证图片后缀
        """
        image_regex = r'.*(.jpg|.png|.gif)$'
        cp = re.compile(image_regex)
        if not cp.match(image_name.lower()):
            # print('图片验证不通过')
            return False
        return True

    def clean_image(self):
        image = self.cleaned_data['image']
        # print(image)
        if not image or self.valid_image(image.name) is False:
            raise forms.ValidationError('请选择jpg、png或gif格式的图片')
        return image


# 个人信息修改表单
class UserCenterInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('nick_name', 'gender', 'birthday', 'address', 'mobile')
