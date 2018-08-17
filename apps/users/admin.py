from django.contrib import admin

from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    pass


# 将UserProfile注册进我们的admin中, 并为它选择管理器
admin.site.register(UserProfile, UserProfileAdmin)