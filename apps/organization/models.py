from django.db import models
from datetime import datetime


# 城市信息，用户课程机构所在城市选择
class CityDict(models.Model):
    name = models.CharField(max_length=20, verbose_name='城市')
    desc = models.TextField(verbose_name='描述')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name_plural= verbose_name = '城市'

    def __str__(self):
        return self.name


# 课程机构信息
class CourseOrg(models.Model):
    ORG_CHOICES = (
        ("pxjg", "培训机构"),
        ("gx", "高校"),
        ("gr", "个人"),
    )

    name = models.CharField(max_length=50, verbose_name='机构名称')
    desc = models.TextField(verbose_name='机构描述')
    category = models.CharField(choices=ORG_CHOICES, max_length=10, default='pxjg', verbose_name='机构类别')
    click_nums = models.IntegerField(default=0, verbose_name='点击数')
    fav_nums = models.IntegerField(default=0, verbose_name='收藏数')
    students = models.IntegerField(default=0, verbose_name='学习人数')
    course_nums = models.IntegerField(default=0, verbose_name='课程数')
    image = models.ImageField(upload_to='org/%Y/%m', max_length=100, blank=True, null=True, verbose_name='封面图')
    address = models.CharField(max_length=150, verbose_name='机构地址')
    city = models.ForeignKey(CityDict, on_delete=models.CASCADE, verbose_name='所在城市')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name_plural = verbose_name = '课程机构'

    def get_teacher_nums(self):
        return self.teachers.count()

    def change_fav_nums(self, add=1):
        self.fav_nums += add
        if self.fav_nums < 0:
            self.fav_nums = 0
        self.save(update_fields=['fav_nums'])

    def __str__(self):
        return self.name


# 机构里的讲师信息
class Teacher(models.Model):
    org = models.ForeignKey(CourseOrg, on_delete=models.CASCADE, related_name='teachers', verbose_name='所属机构')
    name = models.CharField(max_length=50, verbose_name='讲师名称')
    work_years = models.IntegerField(default=0, verbose_name='工作年限')
    work_company = models.CharField(max_length=50, verbose_name='就职公司')
    work_position = models.CharField(max_length=50, verbose_name='公司职位')
    points = models.CharField(max_length=50, verbose_name=u"教学特点")
    click_nums = models.IntegerField(default=0, verbose_name=u"点击数")
    fav_nums = models.IntegerField(default=0, verbose_name=u"收藏数")
    add_time = models.DateTimeField(default=datetime.now, verbose_name=u"添加时间")
    image = models.ImageField(upload_to='teacher/%Y/%m', null=True, blank=True, max_length=100, verbose_name='讲师头像')

    class Meta:
        verbose_name_plural = verbose_name = '讲师'

    def __str__(self):
        return self.name


