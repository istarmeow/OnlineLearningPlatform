from django.shortcuts import render, HttpResponse, HttpResponseRedirect, reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic import View
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin  # 需要登录才能访问
from django.conf import settings
import os
import json

from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

from .models import UserProfile, EmailVerifyRecord
from .forms import LoginForm, RegisterForm, ForgetPwdForm, ModifyPwdForm, UserImageUploadForm, UserCenterInfoForm
from utils.email_send import send_register_email
from operation.models import UserCourse, UserFavorite, UserMessage
from courses.models import Course
from organization.models import Teacher, CourseOrg
from users.models import Banner


# 自定义登录，可使用邮箱和账号
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 不希望用户存在两个，get只能有一个。两个是get失败的一种原因 Q为使用并集查询
            user = UserProfile.objects.get(Q(username=username) | Q(email=username))

            # django的后台中密码加密：所以不能password==password
            # UserProfile继承的AbstractUser中有def check_password(self, raw_password)

            if user.check_password(password):
                return user
        except Exception as e:
            return None


# 当我们配置url被这个view处理时，自动传入request对象
def user_login(request):
    if request.method == 'POST':
        user_name = request.POST.get('username', '')
        pass_word = request.POST.get('password', '')

        user = authenticate(username=user_name, password=pass_word)

        # 认证成功返回user对象，失败返回null
        if user:
            login(request, user)
            return render(request, 'index.html')
        else:
            return render(request, 'login.html',
                          {
                              'msg': '用户名或密码错误!'
                          })

    elif request.method == 'GET':
        return render(request, 'login.html', {})


# 基于类的视图实现登录
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html', {})

    def post(self, request):
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            user_name = request.POST.get('username', '')
            pass_word = request.POST.get('password', '')

            user = authenticate(username=user_name, password=pass_word)

            # 认证成功返回user对象，失败返回null
            if user:
                login(request, user)
                # return render(request, 'index.html')
                return HttpResponseRedirect(reverse('index'))
            else:
                return render(request, 'login.html',
                              {
                                  'msg': '用户名或密码错误!',
                                  'login_form': login_form,
                              })
        else:
            return render(request, 'login.html',
                          {
                              'login_form': login_form,
                          })


# 用户退出
class LogoutView(View):
    def get(self, request):
        logout(request)
        # 把url名称反解成整个url地址，然后供HttpResponseRedirect调用
        from django.urls import reverse
        return HttpResponseRedirect(reverse('index'))


# 用户注册
class RegisterView(View):
    def get(self, request):
        # print(request.build_absolute_uri())  # 地址为：  http://127.0.0.1:8000/register/
        register_form = RegisterForm()
        # 图片验证码
        # hashkey验证码生成的秘钥，image_url验证码的图片地址
        hashkey = CaptchaStore.generate_key()
        image_url = captcha_image_url(hashkey)

        return render(request, 'register.html',
                      {
                          'register_form': register_form,
                          'hashkey': hashkey,
                          'image_url': image_url,
                      })

    def post(self, request):
        register_form = RegisterForm(request.POST)

        # 图片验证码
        hashkey = CaptchaStore.generate_key()
        image_url = captcha_image_url(hashkey)

        if register_form.is_valid():
            user_name = request.POST.get("email", "")
            pass_word = request.POST.get("password", "")

            # 用户不为空字符串，且用户
            if user_name.strip() != '' and not UserProfile.objects.filter(email=user_name):
                # 实例化一个user_profile对象，将前台值存入
                user_profile = UserProfile()
                user_profile.username = user_name
                user_profile.email = user_name

                # 加密password进行保存
                user_profile.password = make_password(pass_word)
                # 默认激活状态True，需要改为False
                user_profile.is_active = False
                user_profile.save()

                # 写入欢迎注册消息到用户消息
                user_message = UserMessage()
                user_message.user = user_profile.id  # 接收用户的id
                user_message.message = '欢迎注册在线学习平台'
                user_message.save()

                # 发送注册激活邮件
                send_register_email(request_uri=request.build_absolute_uri(), email=user_name, send_type='register')

                return render(request, 'login.html')
            else:
                return render(request, 'register.html',
                              {
                                  'register_form': register_form,
                                  'msg': '邮箱已使用！',
                                  'hashkey': hashkey,
                                  'image_url': image_url,
                              })

        return render(request, 'register.html',
                      {
                          'register_form': register_form,
                          'hashkey': hashkey,
                          'image_url': image_url,
                      })


# 激活用户
class ActiveUserView(View):
    def get(self, request, active_code):
        # 查询验证码是否存在
        all_record = EmailVerifyRecord.objects.filter(code=active_code)

        if all_record:
            for record in all_record:
                email = record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
                return render(request, 'login.html',
                              {
                                  'msg': '激活用户成功'
                              })
        else:
            register_form = RegisterForm()
            hashkey = CaptchaStore.generate_key()
            image_url = captcha_image_url(hashkey)

            return render(request, 'register.html',
                          {
                              "msg": "您的激活链接无效",
                              'register_form': register_form,
                              'hashkey': hashkey,
                              'image_url': image_url,
                          })


# 忘记密码视图
class ForgetPwdView(View):
    def get(self, request):
        # print(request.build_absolute_uri())
        forgetpwd_form = ForgetPwdForm()
        # 图片验证码
        hashkey = CaptchaStore.generate_key()
        image_url = captcha_image_url(hashkey)
        return render(request, 'forgetpwd.html',
                      {
                          'forgetpwd_form': forgetpwd_form,
                          'hashkey': hashkey,
                          'image_url': image_url,
                      })

    def post(self, request):
        forgetpwd_form = ForgetPwdForm(request.POST)
        # 图片验证码
        hashkey = CaptchaStore.generate_key()
        image_url = captcha_image_url(hashkey)

        if forgetpwd_form.is_valid():
            email = request.POST.get('email', '')
            if UserProfile.objects.filter(email=email):
                # 如果邮箱是注册过的，就发送改密邮件，然后跳回登录页面
                send_register_email(request_uri=request.build_absolute_uri(), email=email, send_type='forget')

                return render(request, 'login.html',
                              {
                                  'msg': '重置密码邮件已发送,请注意查收',
                              })
            else:
                return render(request, 'forgetpwd.html',
                              {
                                  'forgetpwd_form': forgetpwd_form,
                                  'hashkey': hashkey,
                                  'image_url': image_url,
                                  'msg': '邮箱未注册，请检查是否输入错误'
                              })
        else:
            return render(request, 'forgetpwd.html',
                          {
                              'forgetpwd_form': forgetpwd_form,
                              'hashkey': hashkey,
                              'image_url': image_url,
                          })


# 重置密码
class RestpwdView(View):
    def get(self, request, active_code):
        # 查询验证码是否存在
        all_record = EmailVerifyRecord.objects.filter(code=active_code)

        if all_record:
            for record in all_record:
                email = record.email

                return render(request, 'pwdreset.html',
                              {
                                  'email': email
                              })
        else:
            forgetpwd_form = ForgetPwdForm()
            hashkey = CaptchaStore.generate_key()
            image_url = captcha_image_url(hashkey)

            return render(request, 'forgetpwd.html',
                          {
                              'forgetpwd_form': forgetpwd_form,
                              "msg": "您的重置链接无效",
                              'hashkey': hashkey,
                              'image_url': image_url,
                          })


# 密码重置后修改密码
class ModifypwdView(View):
    def post(self, request):
        modifypwd_form = ModifyPwdForm(request.POST)

        if modifypwd_form.is_valid():
            pwd1 = request.POST.get("password", "")
            pwd2 = request.POST.get("re_password", "")
            email = request.POST.get("email", "")
            # 如果两次密码不相等，返回错误信息
            if pwd1 != pwd2:
                return render(request, "pwdreset.html",
                              {
                                  "email": email,
                                  "msg": "密码不一致",
                                  'modifypwd_form': modifypwd_form,
                               })
            # 如果密码一致
            user = UserProfile.objects.get(email=email)
            # 加密成密文
            user.password = make_password(pwd2)
            # save保存到数据库
            user.save()
            return render(request, "login.html", {"msg": "密码修改成功，请登录"})
        else:
            email = request.POST.get("email", "")
            return render(request, 'pwdreset.html',
                          {
                              'email': email,
                              'modifypwd_form': modifypwd_form,
                          })


# 用户中心个人信息
class UserCenterInfoView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        return render(request, 'usercenter-info.html', locals())

    def post(self, request):
        user_center_info_form = UserCenterInfoForm(request.POST, instance=request.user)  # 传递一个user实例，否则是新增，而不是修改
        if user_center_info_form.is_valid():
            user_center_info_form.save()
            return HttpResponse('{"info_save_status":"success", "info_save__msg":"用户信息更新成功"}', content_type='application/json')
        else:
            user_center_info_errors = json.dumps(user_center_info_form.errors, ensure_ascii=False)
            print(user_center_info_errors)
            return HttpResponse(user_center_info_errors, content_type='application/json')


# 用户修改密码
class UserModifypwdView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request):
        modifypwd_form = ModifyPwdForm(request.POST)

        if modifypwd_form.is_valid():
            pwd1 = request.POST.get("password", "")
            pwd2 = request.POST.get("re_password", "")
            # 如果两次密码不相等，返回错误信息
            if pwd1 != pwd2:
                return HttpResponse('{"modify_status":"fail", "modify_msg":"两次密码不一致"}', content_type='application/json')
            # 如果密码一致
            user = request.user
            # 加密成密文
            user.password = make_password(pwd2)
            # save保存到数据库
            user.save()
            return HttpResponse('{"modify_status":"success", "modify_msg":"密码修改成功"}', content_type='application/json')
        else:
            return HttpResponse('{"modify_status":"fail", "modify_msg":"密码不符合要求"}', content_type='application/json')


# 用户上传图片
class UserImageUploadView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request):
        print('即将上传图片')
        # 这时候用户上传的文件就已经被保存到image_upload_form了 ，为modelform添加instance值直接保存
        image_upload_form = UserImageUploadForm(request.POST, request.FILES)

        if image_upload_form.is_valid():
            # 对原头像进行删除
            base_dir = settings.BASE_DIR
            # print(base_dir)
            user_image_path = request.user.image.path
            # print(user_image_path)
            user_absolute_path = os.path.join(base_dir, user_image_path)
            print(user_absolute_path)
            if os.path.exists(user_absolute_path):
                # print('头像存在，正在删除')
                os.remove(user_absolute_path)

            # 上传新头像保存
            # print(image_upload_form.cleaned_data['image'])
            image = image_upload_form.cleaned_data['image']
            request.user.image = image
            request.user.save()
            return HttpResponse('{"upload_status":"success", "upload_msg":"头像上传成功，自动修改头像", "image_url": "' + request.user.image.url + '"}', content_type='application/json')
        else:
            print('图片上传失败', image_upload_form.errors)
            return HttpResponse('{"upload_status":"fail", "upload_msg":"头像上传失败"}', content_type='application/json')


# 修改邮箱发送验证码
class ModifyEmailSendCodeView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        new_email = request.GET.get('new_email', '').strip()
        if new_email == '':
            return HttpResponse('{"email_status":"fail", "email_msg":"邮箱不能为空"}', content_type='application/json')
        elif UserProfile.objects.filter(email=new_email):
            return HttpResponse('{"email_status":"fail", "email_msg":"邮箱已存在"}', content_type='application/json')
        else:
            if send_register_email(request_uri=request.build_absolute_uri(), email=new_email, send_type='update_email'):
                return HttpResponse('{"email_status":"success", "email_msg":"邮件发送成功，请注意查收"}', content_type='application/json')
            else:
                return HttpResponse('{"email_status":"fail", "email_msg":"邮箱可能格式错误，发送失败"}', content_type='application/json')


# 保存修改的邮箱
class SaveEmailModifyView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def post(self, request):
        new_email = request.POST.get('new_email', '').strip()
        verification_code = request.POST.get('code', '').strip()

        # 查询验证码是否存在
        existed_record = EmailVerifyRecord.objects.filter(code=verification_code, email=new_email, send_type='update_email')

        if existed_record:
            user = request.user
            user.email = new_email
            user.save()
            return HttpResponse('{"save_email_status":"success", "save_email_msg":"邮箱已更新"}', content_type='application/json')
        else:
            return HttpResponse('{"save_email_status":"fail", "save_email_msg":"邮箱验证失败"}', content_type='application/json')


# 我的课程
class MyCourseView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        all_user_course = UserCourse.objects.filter(user=request.user)
        return render(request, 'usercenter-course.html', locals())


# 我的收藏
class MyFavoriteView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        # 获取所有用户收藏的课程
        all_user_fav_course = UserFavorite.objects.filter(user=request.user, fav_type=1)
        all_fav_course = [Course.objects.get(id=user_fav_course.fav_id) for user_fav_course in all_user_fav_course]

        # 获取所有用户收藏的讲师
        all_user_fav_teacher = UserFavorite.objects.filter(user=request.user, fav_type=3)
        all_fav_teacher = [Teacher.objects.get(id=user_fav_teacher.fav_id) for user_fav_teacher in all_user_fav_teacher]

        # 收藏的机构
        all_user_fav_org = UserFavorite.objects.filter(user=request.user, fav_type=2)
        all_fav_org = [CourseOrg.objects.get(id=user_fav_org.fav_id) for user_fav_org in all_user_fav_org]
        return render(request, 'usercenter-fav.html', locals())


# 用户消息
class MyMessageView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        all_user_msg = UserMessage.objects.all().filter(user=request.user.id)

        # 当访问我的消息时，所有未读消息变为已读
        UserMessage.objects.filter(user=request.user.id, has_read=False).update(has_read=True)

        # 分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从all_course中取8个出来，每页显示8个
        p = Paginator(all_user_msg, 8, request=request)
        all_user_msg = p.page(page)
        return render(request, 'usercenter-msg.html', locals())


class IndexView(View):
    def get(self, request):
        all_banner = Banner.objects.all()
        first_org = CourseOrg.objects.order_by('-students', '-click_nums', '-fav_nums').first()  # 最火机构
        first_teacher = Teacher.objects.order_by('-fav_nums', '-click_nums').first()  # 最强讲师
        # 课程位，取4个进行显示
        courses = Course.objects.all()[:8]
        # 轮播图课程位取1个显示
        banner_course = Course.objects.filter(is_banner=True).first()
        # 课程机构
        course_orgs = CourseOrg.objects.all()
        return render(request, 'index.html', locals())


# 全局404处理函数
def page_not_found(request):
    from django.shortcuts import render_to_response
    response = render_to_response('404.html')
    # 设置response的状态码
    response.status_code = 404
    return response


# 全局500处理函数
def page_error(request):
    from django.shortcuts import render_to_response
    response = render_to_response('500.html')
    # 设置response的状态码
    response.status_code = 500
    return response
