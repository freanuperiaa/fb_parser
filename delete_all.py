from apps.core.models import *


def main():
    FacebookGroup.objects.all().delete()
    Post.objects.all().delete()
    Comment.objects.all().delete()


if __name__ == '__main__':
    main()
