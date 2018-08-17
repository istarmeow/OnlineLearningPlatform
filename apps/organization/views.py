from django.shortcuts import render, HttpResponse
from django.db.models import Q

from django.views.generic.base import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from .models import CourseOrg, CityDict, Teacher
from .forms import UserAskForm
from operation.models import UserFavorite
from courses.models import Course
from organization.models import Teacher


class OrgListView(View):
    def get(self, request):
        # 查找所有的机构
        all_org = CourseOrg.objects.all()
        # 取出所有城市
        all_city = CityDict.objects.all()
        # 机构类别
        all_category = list(map(lambda x: {'code': x[0], 'explain': x[1]}, CourseOrg.ORG_CHOICES))

        # 热门机构，选择点击数最多的3个机构显示到右边
        hot_org = all_org.order_by('-click_nums')[:3]

        # 全局搜索---课程列表
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            # 在name字段进行操作, 做like语句的操作。i代表不区分大小写，or操作使用Q
            all_org = all_org.filter(Q(name__icontains=search_keywords) | Q(desc__icontains=search_keywords))

        # 处理类别筛选，取回的是字符串
        category_code = request.GET.get('category', '')
        if category_code:
            all_org = all_org.filter(category=category_code)

        # 处理城市筛选，取回的是city的ID
        city_id = request.GET.get('city', '')
        if city_id:
            all_org = all_org.filter(city=city_id)

        # 排序，按照学习人数或者课程数排序
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'students':
                all_org = all_org.order_by('-students')
            elif sort == 'courses':
                all_org = all_org.order_by('-course_nums')
            elif sort == 'fav':
                all_org = all_org.order_by('-fav_nums')

        # 机构数量
        org_nums = all_org.count()

        # 对课程机构进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 从列表中取5个出来，也就是每页显示5个
        p = Paginator(all_org, 5, request=request)
        all_org = p.page(page)

        # 标记当前页，用于页面选中active
        current_access_url = 'org'
        return render(request, 'org-list.html', locals())


# 用户咨询表单提交
class AddUserAskView(View):
    def post(self, request):
        userask_form = UserAskForm(request.POST)
        # 判断form是否有效
        if userask_form.is_valid():
            # 这里是modelform和form的区别
            # 它有model的属性
            # 当commit为true进行真正保存
            userask_form.save(commit=True)
            # 这样就不需要把一个一个字段取出来然后存到model的对象中之后save

            # 如果保存成功,返回json字符串,后面content type是告诉浏览器的
            return HttpResponse('{"post_statue": "success", "msg": "Tips：提交成功"}', content_type='application/json')
        else:
            # 如果保存失败，返回json字符串,并将form的报错信息通过msg传递到前端
            return HttpResponse('{"post_statue": "fail", "msg": "Tips：添加出错"}', content_type='application/json')


# 机构首页
class OrgHomeView(View):
    def get(self, request, org_id):
        # 通过id找到机构
        course_org = CourseOrg.objects.get(id=org_id)

        # 点击数+1
        course_org.click_nums += 1
        course_org.save(update_fields=['click_nums'])

        # 通过机构找到这个机构的课程和教师，并按一些数据进行排序
        all_course = course_org.courses.all().order_by('-students', '-fav_nums', 'click_nums')[:4]
        all_teacher = course_org.teachers.all().order_by('-fav_nums', '-click_nums')[:4]

        # TYPE_CHOICES = (
        #     (1, "课程"),
        #     (2, "课程机构"),
        #     (3, "讲师")
        # )
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        # 标记当前页，用于页面选中active
        current_access_url = 'org'
        current_url = 'org_home'
        return render(request, 'org-detail-homepage.html', locals())


# 机构课程详情
class OrgCourseView(View):
    def get(self, request, org_id):
        # 通过id找到机构
        course_org = CourseOrg.objects.get(id=org_id)

        # 通过机构找到这个机构的课程，并按一些数据进行排序
        all_course = course_org.courses.all().order_by('-students')

        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'fav':
                all_course = all_course.order_by('-fav_nums')
            elif sort == 'click':
                all_course = all_course.order_by('click_nums')

        # 机构是否已收藏
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        # 标记当前页，用于页面选中active
        current_access_url = 'org'
        current_url = 'org_course'
        return render(request, 'org-detail-course.html', locals())


# 机构讲师
class OrgTeacherView(View):
    def get(self, request, org_id):
        course_org = CourseOrg.objects.get(id=org_id)

        # 通过机构找到这个机构的教师，并按一些数据进行排序
        all_teacher = course_org.teachers.all().order_by('-click_nums')
        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'fav':
                all_teacher = all_teacher.order_by('-fav_nums')

        # 机构是否已收藏
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        # 标记当前页，用于页面选中active
        current_access_url = 'org'
        current_url = 'org_teacher'
        return render(request, 'org-detail-teacher.html', locals())


# 机构介绍
class OrgDescView(View):
    def get(self, request, org_id):
        course_org = CourseOrg.objects.get(id=org_id)

        # 机构是否已收藏
        has_fav = False
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=course_org.id, fav_type=2):
                has_fav = True

        # 标记当前页，用于页面选中active
        current_access_url = 'org'
        current_url = 'org_desc'
        return render(request, 'org-detail-desc.html', locals())


# 机构收藏或取消收藏
class AddFavView(View):
    # (1, "课程"),
    # (2, "课程机构"),
    # (3, "讲师")

    def post(self, request):
        # 收藏的不管是课程，讲师，还是机构，都是记录他们的id，如果没取到把它设置未0，避免查询时异常
        fav_id = request.POST.get('fav_id', 0)
        # 表明收藏的类别
        fav_type = request.POST.get('fav_type', 0)

        # 收藏与已收藏取消收藏
        # 判断用户是否登录:即使没登录会有一个匿名的user
        if not request.user.is_authenticated:
            # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
            return HttpResponse('{"fav_status":"fail", "fav_msg":"用户未登录"}', content_type='application/json')

        exist_records = UserFavorite.objects.filter(user=request.user, fav_id=fav_id, fav_type=fav_type)

        if exist_records:
            # 如果已经存在，表明用户取消收藏
            exist_records.delete()
            if int(fav_type) == 2:
                # 机构模型中存储的收藏数减1
                CourseOrg.objects.get(id=fav_id).change_fav_nums(add=-1)
            elif int(fav_type) == 1:
                # 课程收藏-1
                course = Course.objects.get(id=fav_type)
                course.fav_nums -= 1
                if course.fav_nums < 0:
                    course.fav_nums = 0  # 避免负数出现
                course.save(update_fields=['fav_nums'])
            elif int(fav_type) == 3:
                # 讲师收藏-1
                teacher = Teacher.objects.get(id=fav_id)
                teacher.fav_nums -= 1
                if teacher.fav_nums < 0:
                    teacher.fav_nums = 0  # 避免负数出现
                teacher.save(update_fields=['fav_nums'])
            return HttpResponse('{"fav_status":"success", "fav_msg":"添加收藏"}', content_type='application/json')
        else:
            user_fav = UserFavorite()
            # 如果取到了id值才进行收藏
            if int(fav_id) > 0 and int(fav_type) > 0:
                user_fav.fav_id = fav_id
                user_fav.fav_type = fav_type
                user_fav.user = request.user
                user_fav.save()

                if int(fav_type) == 2:
                    # 机构模型中存储的收藏数加1
                    CourseOrg.objects.get(id=fav_id).change_fav_nums(add=1)
                elif int(fav_type) == 1:
                    # 课程收藏-1
                    course = Course.objects.get(id=fav_type)
                    course.fav_nums += 1
                    course.save(update_fields=['fav_nums'])
                elif int(fav_type) == 3:
                    # 讲师收藏-1
                    teacher = Teacher.objects.get(id=fav_id)
                    teacher.fav_nums += 1
                    teacher.save(update_fields=['fav_nums'])
                return HttpResponse('{"fav_status":"success", "fav_msg":"取消收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"fav_status":"fail", "fav_msg":"收藏出错"}', content_type='application/json')


# 讲师列表
class TeacherListView(View):
    def get(self, request):
        all_teacher = Teacher.objects.all().order_by('-click_nums')
        teacher_nums = all_teacher.count()

        # 全局搜索---讲师列表
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            # 在name字段进行操作, 做like语句的操作。i代表不区分大小写，or操作使用Q
            all_teacher = all_teacher.filter(Q(name__icontains=search_keywords) |
                                             Q(points__icontains=search_keywords) |
                                             Q(org__name__icontains=search_keywords) |
                                             Q(work_company__icontains=search_keywords) |
                                             Q(work_position__icontains=search_keywords))

        sort = request.GET.get('sort', '')
        if sort:
            if sort == 'fav':
                all_teacher = all_teacher.order_by('-fav_nums')

        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
            # 这里每页显示5个
        p = Paginator(all_teacher, 5, request=request)

        all_teacher_page = p.page(page)

        # 排行榜讲师
        rank_teacher = Teacher.objects.all().order_by("-fav_nums", "click_nums")[:5]

        # 标记当前页，用于页面选中active
        current_access_url = 'teacher'
        return render(request, 'teacher-list.html', locals())


# 讲师详情
class TeacherDetailView(View):
    def get(self, request, teacher_id):
        teacher = Teacher.objects.get(id=teacher_id)

        # 增加讲师的访问量
        teacher.click_nums += 1
        teacher.save(update_fields=['click_nums'])

        # 排行榜讲师
        rank_teacher = Teacher.objects.all().order_by("-fav_nums", "click_nums")[:5]

        # 讲师和机构是否已收藏
        has_fav_teacher = False
        has_fav_org = False

        # 必须是用户已登录我们才需要判断。
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(user=request.user, fav_id=teacher.id, fav_type=3):
                # 该讲师已收藏
                has_fav_teacher = True
            if UserFavorite.objects.filter(user=request.user, fav_id=teacher.org.id, fav_type=2):
                # 该机构已收藏
                has_fav_org = True

        # 标记当前页，用于页面选中active
        current_access_url = 'teacher'
        return render(request, 'teacher-detail.html', locals())