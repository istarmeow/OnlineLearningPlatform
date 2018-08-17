#! /usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path, re_path

from .views import TeacherListView, TeacherDetailView

app_name = 'teacher'

urlpatterns = [
    # 讲师相关url
    path('list/', TeacherListView.as_view(), name='teacher_list'),
    re_path('id/(?P<teacher_id>\d+)/detail/', TeacherDetailView.as_view(), name='teacher_detail'),
]
