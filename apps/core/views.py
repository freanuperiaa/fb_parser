from django.views.generic import TemplateView
from django.views.generic.base import View
from django.shortcuts import redirect

from .forms import ParseForm
from .tasks import scrape, scrape_group


class HomePageView(TemplateView):
    template_name ='core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parse_form'] = ParseForm()
        return context


def start(request):
    if request.method == 'POST':
        data = request.POST.copy()
        user = data.get('username')
        password = data.get('password')
        url = data.get('url')
        if url is '':
            print('start scraping everything')
            scrape.delay(user, password)
            return redirect('/admin/core/post')
        else:
            print('scraping group{}'.format(url))
            scrape_group.delay(user, password, url)
            return redirect('/admin/core/post')
