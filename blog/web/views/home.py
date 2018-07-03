#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.shortcuts import render
from django.shortcuts import redirect
from repository import models
from utils.pagination import Pagination
from django.urls import reverse
import time
from django.db import connection


def index(request, *args, **kwargs):
    """
    博客首页，展示全部博文
    :param request:
    :return:
    """

    article_type_list = models.Article.type_choices

    if kwargs:
        article_type_id = int(kwargs['article_type_id'])
        base_url = reverse('index',kwargs=kwargs)
    else:
        article_type_id = None
        base_url = '/'

    data_count = article_list = models.Article.objects.filter(**kwargs).count()

    page_obj = Pagination(request.GET.get('p'),data_count)
    #当前页所要显示的信息
    article_list = models.Article.objects.filter(**kwargs).order_by('-nid')[page_obj.start:page_obj.end]
    #显示的页码数
    page_str = page_obj.page_str(base_url)

    return render(
        request,
        'index.html',
        {
            'article_list': article_list,
            'article_type_id': article_type_id,
            'article_type_list': article_type_list,
            'page_str': page_str,
        }
    )


def home(request, site):
    """
    博主个人首页
    :param request:
    :param site: 博主的网站后缀如：http://xxx.com/wupeiqi.html
    :return:
    """
    blog = models.Blog.objects.filter(site=site).select_related('user').first()
    if not blog:
        return redirect('/')
    tag_list = models.Tag.objects.filter(blog=blog)
    category_list = models.Category.objects.filter(blog=blog)
    # date_format(create_time,"%Y-%m")

    query =  'select nid, count(nid) as num,strftime("%Y-%m",create_time/1000,"unixepoch","localtime") as ctime from repository_article group by strftime("%Y-%m",create_time/1000,"unixepoch","localtime")'
    wi  =  'select * from repository_article WHERE blog_id=%s'%blog.nid

    date_list = models.Article.objects.raw( query )
    person_data_list ={}
    for item in date_list:
        person_list = models.Article.objects.filter(blog=blog).extra(
            where=['strftime("%%Y-%%m", create_time / 1000, "unixepoch", "localtime")=%s'], params=[item.ctime, ]).all()
        person_data_list[item.ctime] = person_list.count()

    for k,v in person_data_list.items():
        print(k,v)
    article_list = models.Article.objects.filter(blog=blog).order_by('-nid').all()

    return render(
        request,
        'home.html',
        {
            'blog': blog,
            'tag_list': tag_list,
            'category_list': category_list,
            'date_list': person_data_list,
            'article_list': article_list
        }
    )


def filter(request, site, condition, val):
    """
    分类显示
    :param request:
    :param site:
    :param condition:
    :param val:
    :return:
    """
    # 找到用户和个人博客标题前缀（url后面添加）
    blog = models.Blog.objects.filter(site=site).select_related('user').first()
    #如果没有显示首页
    if not blog:
        return redirect('/')
    #找到所属博客的标签
    tag_list = models.Tag.objects.filter(blog=blog)
    #所属博客分类
    category_list = models.Category.objects.filter(blog=blog)
    #所有用户的博客按日期分类
    # date_list = models.Article.objects.raw(
    #     'select nid, count(nid) as num,strftime("%Y-%m",create_time/1000,"unixepoch","localtime") as ctime from repository_article group by strftime("%Y-%m",create_time/1000,"unixepoch","localtime")')
    query = 'select nid, count(nid) as num,strftime("%Y-%m",create_time/1000,"unixepoch","localtime") as ctime from repository_article group by strftime("%Y-%m",create_time/1000,"unixepoch","localtime")'
    wi = 'select * from repository_article WHERE blog_id=%s' % blog.nid
    # 所有用户的博客按日期分类
    date_list = models.Article.objects.raw(query)
    person_data_list = {}
    #当前用户按日期分类
    for item in date_list:
        person_list = models.Article.objects.filter(blog=blog).extra(
            where=['strftime("%%Y-%%m", create_time / 1000, "unixepoch", "localtime")=%s'], params=[item.ctime, ]).all()
        person_data_list[item.ctime] = person_list.count()

    template_name = "home_summary_list.html"
    if condition == 'tag':
        template_name = "home_title_list.html"
        article_list = models.Article.objects.filter(tags=val, blog=blog).all()
    elif condition == 'category':
        article_list = models.Article.objects.filter(category=val, blog=blog).all()
    elif condition == 'date':
        # article_list = models.Article.objects.filter(blog=blog).extra(
        # where=['date_format(create_time,"%%Y-%%m")=%s'], params=[val, ]).all()

        article_list = models.Article.objects.filter(blog=blog).extra(
            where=['strftime("%%Y-%%m", create_time / 1000, "unixepoch", "localtime")=%s'], params=[val, ]).all()
        # strftime("%%Y-%%m",create_time)=%s
        # strftime("%Y-%m", create_time / 1000, "unixepoch", "localtime")
        # select * from article where strftime("%Y-%m",create_time)=2017-02
        print(article_list.count())
    else:
        article_list = []

    return render(
        request,
        template_name,
        {
            'blog': blog,
            'tag_list': tag_list,
            'category_list': category_list,
            'date_list': person_data_list,
            'article_list': article_list
        }
    )


def detail(request, site, nid):
    """
    博文详细页
    :param request:
    :param site:
    :param nid:
    :return:
    """
    blog = models.Blog.objects.filter(site=site).select_related('user').first()
    tag_list = models.Tag.objects.filter(blog=blog)
    category_list = models.Category.objects.filter(blog=blog)
    # 所有用户的博客按日期分类
    # date_list = models.Article.objects.raw(
    #     'select nid, count(nid) as num,strftime("%Y-%m",create_time/1000,"unixepoch","localtime") as ctime from repository_article group by strftime("%Y-%m",create_time/1000,"unixepoch","localtime")')
    query = 'select nid, count(nid) as num,strftime("%Y-%m",create_time/1000,"unixepoch","localtime") as ctime from repository_article group by strftime("%Y-%m",create_time/1000,"unixepoch","localtime")'
    wi = 'select * from repository_article WHERE blog_id=%s' % blog.nid
    # 所有用户的博客按日期分类
    date_list = models.Article.objects.raw(query)
    person_data_list = {}
    # 当前用户按日期分类
    for item in date_list:
        person_list = models.Article.objects.filter(blog=blog).extra(
            where=['strftime("%%Y-%%m", create_time / 1000, "unixepoch", "localtime")=%s'], params=[item.ctime, ]).all()
        person_data_list[item.ctime] = person_list.count()

    article = models.Article.objects.filter(blog=blog, nid=nid).select_related('category', 'articledetail').first()
    comment_list = models.Comment.objects.filter(article=article).select_related('reply')
    return render(
        request,
        'home_detail.html',
        {
            'blog': blog,
            'article': article,
            'comment_list': comment_list,
            'tag_list': tag_list,
            'category_list': category_list,
            'date_list': person_data_list,
        }

    )

