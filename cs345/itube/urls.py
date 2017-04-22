"""cs345 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
import itube.views as itube_views
import django.contrib.auth.views as auth_views

urlpatterns = [
    url(r'index/$', itube_views.index, name='index'),
    url(r'login/$', itube_views.login_view, name='login'),
    url(r'signup/$', itube_views.signup_view, name='signup'),
    url(r'logout/$', itube_views.logout_view, name='logout'),
    url(r'new/$', itube_views.new_view, name='new_view'),
    url(r'like/$', itube_views.like_view, name='like_view'),
    url(r'fav/$', itube_views.fav, name='fav_view'),

    url(r'get_query/$', itube_views.get_query_view, name='like_view'),
    url(r'category/$', itube_views.category_view, name='category_view'),
    
    


    #url(r'index/(?P<id>=[0-9a-zA-Z_-]+)', itube_views.index2, name='index'),
]
