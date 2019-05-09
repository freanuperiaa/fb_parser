from django.contrib import admin

from .models import FacebookGroup, Post, Comment

admin.site.register(FacebookGroup)
admin.site.register(Post)
admin.site.register(Comment)