from django.db import models


class FacebookPage(models.Model):
    name = models.CharField(max_length=150)
    url = models.URLField(unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=100)
    url = models.URLField(unique=True, default='')
    group = models.ForeignKey(
        FacebookPage, on_delete=models.SET_NULL, null=True,
        related_name='posts'
    )
    author = models.CharField(max_length=75)
    author_url = models.URLField()
    description = models.TextField()
    total_reacts = models.CharField(max_length=10)
    likes = models.CharField(max_length=10)
    heart = models.CharField(max_length=10)
    wow = models.CharField(max_length=10)
    haha = models.CharField(max_length=10)
    sad = models.CharField(max_length=10)
    angry = models.CharField(max_length=10)

    def __str__(self):
        return '{} - {}'.format(self.title, self.author)


class Comment(models.Model):
    author = models.CharField(max_length=75)
    text = models.TextField()
    time = models.CharField(max_length=50)
    no_reacts = models.CharField(max_length=15)
    post = models.ForeignKey(
        Post, on_delete=models.SET_NULL,  null=True, blank=True,
        related_name='comments'
    )

    def __str__(self):
        return self.text
