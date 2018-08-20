from django.db import models
from datetime import datetime

from organization.models import CourseOrg, Teacher


# 课程类别
class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='课程类别')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = verbose_name_plural = '课程类别'

    def __str__(self):
        return self.name


# 课程类别
class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='课程标签')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name = verbose_name_plural = '课程标签'

    def __str__(self):
        return self.name


# 课程信息表
class Course(models.Model):
    DEGREE_CHOICES = (
        ("cj", "初级"),
        ("zj", "中级"),
        ("gj", "高级")
    )
    name = models.CharField(max_length=50, verbose_name='课程名')
    desc = models.CharField(max_length=300, verbose_name='课程描述')
    # 后面会改为富文本
    detail = models.TextField(verbose_name='课程详情')
    degree = models.CharField(max_length=3, choices=DEGREE_CHOICES, verbose_name='课程难度')
    learn_times = models.IntegerField(default=0, verbose_name='学习时长(分钟数)')
    # 点击开始学习后记录学习人数
    students = models.IntegerField(default=0, verbose_name='学习人数')
    fav_nums = models.IntegerField(default=0, verbose_name='收藏人数')
    image = models.ImageField(upload_to='course/%Y/%m', max_length=100, blank=True, null=True, verbose_name='封面图(160*160px)')
    # 点击到课程信息界面即需要记录点击数
    click_nums = models.IntegerField(default=0, verbose_name='点击数')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')
    course_org = models.ForeignKey(CourseOrg, null=True, blank=True, related_name='courses', on_delete=models.CASCADE, verbose_name='所属机构')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='courses', verbose_name='课程类别')  # 课程类别删除后课程该字段设置为null
    tags = models.ManyToManyField(Tag, related_name='courses', blank=True, verbose_name='课程标签')
    teacher = models.ForeignKey(Teacher, related_name='courses', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='讲师')
    notes = models.CharField(max_length=20, default='人生苦短，我用Python！', verbose_name='课程须知')
    tell_you = models.CharField(max_length=20, default='', verbose_name='讲师告诉你学到了什么')
    is_banner = models.BooleanField(default=False, verbose_name='是否轮播')

    class Meta:
        verbose_name = verbose_name_plural = '课程'

    def get_lesson_nums(self):
        # 获取课程章节数，如果章节模型中未定义关联名称（related_name）则直接使用字段名_set来获取
        return self.lesson_set.all().count()

    def __str__(self):
        return self.name


# 课程章节
class Lesson(models.Model):
    # 一个课程下有多个章节，需要用到一对多的关系，使用外键完成
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')
    name = models.CharField(max_length=100, verbose_name='章节名')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    def get_lesson_video(self):
        # 获取章节视频
        return self.video_set.all()

    class Meta:
        verbose_name_plural = verbose_name = '章节'

    def __str__(self):
        return '课程 ' + self.course.name + '的章节：' + self.name


# 课程视频
class Video(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='章节')
    name = models.CharField(max_length=100, verbose_name='视频名')
    url = models.URLField(null=True, blank=True, verbose_name='访问地址')
    learn_times = models.IntegerField(default=0, verbose_name='学习时长(分钟数)')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name_plural = verbose_name = '视频'

    def __str__(self):
        return '章节 ' + self.lesson.name + '的视频：' + self.name


# 课程资源
class CourseResource(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='课程')
    name = models.CharField(max_length=100, verbose_name='名称')
    # 下载的是文件，需要用到文件下载FileField，在后台管理中会自动生成文件上传的按钮
    download = models.FileField(upload_to='course/resource/%Y/%m', max_length=100, verbose_name='资源文件')
    add_time = models.DateTimeField(default=datetime.now, verbose_name='添加时间')

    class Meta:
        verbose_name_plural = verbose_name = '课程资源'

    def __str__(self):
        return '课程 ' + self.course.name + '的资源：' + self.name
