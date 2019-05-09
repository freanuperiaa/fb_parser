from django.contrib import admin

from .models import FacebookPage, Post, Comment

admin.site.register(FacebookPage)
admin.site.register(Post)
admin.site.register(Comment)