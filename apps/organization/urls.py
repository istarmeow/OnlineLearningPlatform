#! /usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path, re_path

from organization.views import OrgListView, AddUserAskView, OrgHomeView, OrgCourseView, OrgDescView, OrgTeacherView, AddFavView

app_name = 'organization'

urlpatterns = [
    # 课程机构列表url
    path('list/', OrgListView.as_view(), name="org_list"),
    path('add_ask/', AddUserAskView.as_view(), name='add_ask'),
    re_path('home/(?P<org_id>\d+)/', OrgHomeView.as_view(), name='org_home'),  # 机构详情首页
    re_path('id/(?P<org_id>\d+)/courses/', OrgCourseView.as_view(), name='org_course'),  # 机构课程列表
    re_path('id/(?P<org_id>\d+)/desc/', OrgDescView.as_view(), name='org_desc'),  # 机构介绍
    re_path('id/(?P<org_id>\d+)/teacher/', OrgTeacherView.as_view(), name='org_teacher'),  # 机构讲师
    path('add_fav/', AddFavView.as_view(), name="add_fav"),  # 添加机构收藏
]
