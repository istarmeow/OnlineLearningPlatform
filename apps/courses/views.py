from django.shortcuts import render, HttpResponse
from django.views.generic.base import View
from django.utils import timezone
from django.db.models.aggregates import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from .models import Course, Tag, Video
from operation.models import UserFavorite
from operation.models import UserCourse, CourseComments


class CourseListView(View):
    def get(self, request):
        all_degree = list(map(lambda x: {'code': x[0], 'explain': x[1]}, Course.DEGREE_CHOICES))  # 显示难度等级

        all_course = Course.objects.all().order_by('-add_time')  # 默认按照时间排序

        # 全局搜索---课程列表
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            # 在name字段进行操作, 做like语句的操作。i代表不区分大小写，or操作使用Q
            all_course = all_course.filter(Q(name__icontains=search_keywords) | Q(desc__icontains=search_keywords) | Q(detail__icontains=search_keywords))

        degree_code = request.GET.get('degree', '')
        if degree_code:
            all_course = all_course.filter(degree=degree_code)

        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'fav':
                all_course = all_course.order_by('-fav_nums')  # 收藏人数排序
            elif sort == 'click':
                all_course = all_course.order_by('-click_nums')  # 点击数排序
            elif sort == 'students':
                all_course = all_course.order_by('-students')  # 按学习人数排序

        course_nums = all_course.count()  # 课程筛选后的数量

        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从all_course中取8个出来，每页显示8个
        p = Paginator(all_course, 8, request=request)
        all_course_page = p.page(page)

        hot_course = Course.objects.all().order_by('-students')[:3]  # 热门课程选择3个显示

        # 标记当前页，用于页面选中active
        current_access_url = 'course'

        # 当前时间
        time_now = timezone.now()
        return render(request, 'course-list.html', locals())


# 单个课程详情
class CourseDetailView(View):
    def get(self, request, course_id):
        course = Course.objects.get(id=course_id)

        # 增加课程点击数
        course.click_nums += 1
        course.save(update_fields=['click_nums'])

        # 相关推荐
        course_tags_ids = course.tags.values_list('id', flat=True)  # 获取当前课程所有标签的id
        similar_course = Course.objects.filter(tags__in=course_tags_ids).exclude(id=course.id)  # 获取包含这些标签的课程并排除当前课程
        similar_course = similar_course.annotate(same_tags=Count('tags')).order_by('-same_tags', '-students')[:3]  # 使用Count聚合函数来生成一个计算字段same_tags

        # 学习该课程的用户，首先获取该课程在UserCourse对应关系，然后查询UserCourse表中的所有用户，使用distinct()去重
        user_courses = UserCourse.objects.filter(course=course)
        # print(user_courses)
        user_courses = user_courses.values('user__nick_name', 'user__username', 'user__image').distinct()
        # print(user_courses)

        # 课程和机构是否已收藏
        has_fav_course = False
        has_fav_org = False

        # 必须是用户已登录我们才需要判断。
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course.id, fav_type=1):
                # 该课程已收藏
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user, fav_id=course.course_org.id, fav_type=2):
                # 该机构已收藏
                has_fav_org = True

        # 标记当前页，用于页面选中active
        current_access_url = 'course'
        return render(request, 'course-detail.html', locals())


# 课程内容---章节、视频、资源、相关推荐
class CourseContentView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'  # url参数，例如/login/?next=/course/id/1/content/

    def get(self, request, course_id, **kwargs):  # kwargs 专用于获取视频id的
        course = Course.objects.get(id=course_id)

        # 查询用户和该课程是否关联，如果不存在，则创建关联
        has_user_course = UserCourse.objects.filter(user=request.user, course=course)
        if not has_user_course:
            UserCourse.objects.create(user=request.user, course=course)
            # 然后课程的学习人数+1
            course.students += 1
            course.save(update_fields=['students'])

        # 获取该课程的所有章节
        all_lesson = course.lesson_set.all()

        # 获取该课程所有的下载资源
        all_resource = course.courseresource_set.all()

        # 获取该课程所有的评论
        all_comment = course.coursecomments_set.all().order_by('-add_time')
        comment_nums = all_comment.count()
        # 评论分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 每页显示5个
        p = Paginator(all_comment, 5, request=request)
        all_comment_page = p.page(page)

        # tab选择标识，当进入分页的时候，说明已经进入评论页面，则在模板中需要active tab
        if request.GET.get('page'):
            tab_choose = 'comment'

        # 学习该课程的人还学过？
        # 获取该课程的用户课程对应关系
        all_user_course = UserCourse.objects.filter(course=course)
        # 获取该课程的所有用户
        all_user = [user_course.user for user_course in all_user_course]
        # 获取这些用户在用户课程对应关系表中学习的所有课程，并排除当前课程
        related_user_course = UserCourse.objects.filter(user__in=all_user).exclude(course=course)
        # 获取所有关联课程的id
        related_course_id = [user_course.course.id for user_course in related_user_course]
        # 获取关联课程id在课程模型中的查询集，并且按照学习人数排序，取前5个
        related_course = Course.objects.filter(id__in=related_course_id).order_by('-students')[:5]
        # print(related_course)

        # -------------------------
        # 处理访问video的页面
        print(kwargs)
        show_video = False  # 显示课程横幅，而不显示课程视频
        video = None
        video_id = kwargs.get('video_id')
        if video_id:
            show_video = True  # 显示课程视频播放，隐藏课程横幅
            video = Video.objects.get(id=video_id)
        # -------------------------

        # 标记当前页，用于页面选中active
        current_access_url = 'course'
        return render(request, 'course-content.html', locals())


# 添加评论
class AddCommentView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
            return HttpResponse('{"comment_status":"fail", "comment_msg":"用户未登录"}', content_type='application/json')
        course_id = request.POST.get('course_id', 0)
        comments = request.POST.get('comments', '')
        if int(course_id) > 0 and comments.strip():
            course_comment = CourseComments()

            course_comment.course = Course.objects.get(id=course_id)
            course_comment.comments = comments
            course_comment.user = request.user
            course_comment.save()
            return HttpResponse('{"comment_status":"success", "comment_msg":"评论成功"}', content_type='application/json')
        else:
            return HttpResponse('{"comment_status":"fail", "comment_msg":"评论失败"}', content_type='application/json')

