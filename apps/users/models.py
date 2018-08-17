# 第一块区域import官方包
from datetime import datetime
# 第二块区域import第三方包
from django.db import models
from django.contrib.auth.models import AbstractUser
# 第三块区域import自己定义的


class UserProfile(AbstractUser):
    # 自定义的性别选择规则
    GENDER_CHOICES = (
        ('male', '男'),
        ('female', '女')
    )
    nick_name = models.CharField(max_length=50, default='', verbose_name='昵称')
    birthday = models.DateField(null=True, blank=True, verbose_name='生日')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male', verbose_name='性别')
    address = models.CharField(max_length=100, default='', verbose_name='地址')
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='电话')
    image = models.ImageField(upload_to='image/%Y/%m', default='image/default.jpg', blank=True, null=True, max_length=100, verbose_name='头像')

    def get_unread_nums(self):
        # 获取用户未读消息，import需要放在这儿，如果放在头部，会产生循环import
        from operation.models import UserMessage
        return UserMessage.objects.filter(user=self.id, has_read=False).count()

    # Meta信息，即后台栏目名
    class Meta:
        verbose_name_plural = verbose_name = '用户信息'

    def __str__(self):
        return self.username


class EmailVerifyRecord(models.Model):
    SEND_CHOICES = (
        ("register", "注册"),
        ("forget", "找回密码"),
        ("update_email", '修改邮箱')
    )
    code = models.CharField(max_length=20, verbose_name='验证码')
    email = models.EmailField(max_length=50, verbose_name='邮箱')
    send_type = models.CharField(choices=SEND_CHOICES, default='register', max_length=50, verbose_name='发送类型')
    # 这里的now得去掉(), 不去掉会根据编译时间。而不是根据实例化时间
    send_time = models.DateTimeField(default=datetime.now, verbose_name='发送时间')

    class Meta:
        verbose_name_plural = verbose_name = '邮箱验证码'

    def __str__(self):
        return '{}({})'.format(self.code, self.email)


# 1、图片 2. 点击图片地址 3. 轮播图序号(控制前后)
class Banner(models.Model):
    title = models.CharField(max_length=100, verbose_name='标题')
    image = models.ImageField(upload_to='banner/%Y/%m', max_length=100, blank=True, null=True, verbose_name='轮播图')
    url = models.URLField(max_length=200, verbose_name='访问地址')
    # 默认index很大靠后。想要靠前修改index值。
    index = models.IntegerField(default=100, verbose_name='顺序')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name_plural = verbose_name = '轮播图'

    def __str__(self):
        return self.title

