from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=100)
    post_url = models.URLField(unique=True)
    group = models.CharField(max_length=100)
    group_url = models.URLField()
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
    comments = models.ForeignKey(
        to='Comment',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return '{} - {}'.format(self.title, self.author)


class Comment(models.Model):
    author = models.CharField(max_length=75)
    text = models.TextField()
    time = models.CharField(max_length=50)
    no_reacts = models.CharField(max_length=15)

    def __str__(self):
        return self.text
