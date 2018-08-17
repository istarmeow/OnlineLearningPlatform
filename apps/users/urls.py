#! /usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path, re_path

from .views import UserCenterInfoView, UserModifypwdView, UserImageUploadView, ModifyEmailSendCodeView, SaveEmailModifyView, MyCourseView, MyFavoriteView, MyMessageView

app_name = 'users'

urlpatterns = [
    # 用户相关url
    path('info/', UserCenterInfoView.as_view(), name='user_info'),  # 用户信息
    path('password/modify/', UserModifypwdView.as_view(), name='user_modify_pwd'),  # 修改密码
    path('image/upload/', UserImageUploadView.as_view(), name='user_image_upload'),  # 用户上传头像
    path('verify_code/send/', ModifyEmailSendCodeView.as_view(), name='user_send_verify_code'),  # 用户修改邮箱发送验证码
    path('email_modify/save/', SaveEmailModifyView.as_view(), name='user_save_email_modify'),  # 用户保存邮箱修改
    path('my_course/', MyCourseView.as_view(), name='my_course'),  # 我的课程
    path('my_favorite/', MyFavoriteView.as_view(), name='my_favorite'),  # 我的收藏
    path('my_message/', MyMessageView.as_view(), name='my_message'),  # 我的消息
]

