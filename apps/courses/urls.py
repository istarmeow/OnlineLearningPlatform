from django.urls import path, re_path

from .views import CourseListView, CourseDetailView, CourseContentView, AddCommentView

app_name = 'courses'

urlpatterns = [
    # 课程相关url
    path('list/', CourseListView.as_view(), name='course_list'),
    re_path('id/(?P<course_id>\d+)/detail/', CourseDetailView.as_view(), name="course_detail"),  # 课程详情
    re_path('id/(?P<course_id>\d+)/content/', CourseContentView.as_view(), name="course_content"),  # 课程内容
    path('add_comment/', AddCommentView.as_view(), name="add_comment"),  # 添加评论，参数放在post中的
    re_path('id/(?P<course_id>\d+)/video/(?P<video_id>\d+)/', CourseContentView.as_view(), name="video_content"),  # 课程视频播放
]
