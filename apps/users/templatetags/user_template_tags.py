#! /usr/bin/env python
# -*- coding: utf-8 -*-

from django import template

from operation.models import UserFavorite
from courses.models import Course
from organization.models import Teacher, CourseOrg


register = template.Library()  # 只有向系统注册过的tags，系统才认得你


@register.simple_tag
def get_user_fav(user):
    # 获取所有用户收藏的课程
    all_user_fav_course = UserFavorite.objects.filter(user=user, fav_type=1)
    all_fav_course = [Course.objects.get(id=user_fav_course.fav_id) for user_fav_course in all_user_fav_course]

    # 获取所有用户收藏的讲师
    all_user_fav_teacher = UserFavorite.objects.filter(user=user, fav_type=3)
    all_fav_teacher = [Teacher.objects.get(id=user_fav_teacher.fav_id) for user_fav_teacher in all_user_fav_teacher]

    # 收藏的机构
    all_user_fav_org = UserFavorite.objects.filter(user=user, fav_type=2)
    all_fav_org = [CourseOrg.objects.get(id=user_fav_org.fav_id) for user_fav_org in all_user_fav_org]

    return all_fav_course[:3], all_fav_teacher[:3], all_fav_org[:3], len(all_fav_course) + len(all_fav_teacher) + len(all_fav_org)
