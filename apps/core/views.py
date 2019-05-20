from django.urls import reverse
from django.views import generic

from .forms import ParseForm
from .tasks import scrape, scrape_group


class ParseView(generic.FormView):
    form_class = ParseForm
    template_name = 'core/home.html'

    def form_valid(self, form):
        if form.cleaned_data['url'] == '':
            print('start scraping everything')
            scrape.delay(**form.cleaned_data)
        else:
            print('scraping group{}'.format(form.cleaned_data['url']))
            scrape_group.delay(**form.cleaned_data)
        return super(ParseView, self).form_valid(form)

    def get_success_url(self):
        return reverse('admin:core_post_changelist')
