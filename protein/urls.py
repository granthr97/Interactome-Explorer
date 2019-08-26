from django.urls import path, include

from django.contrib import admin
from django.views.generic.base import RedirectView

admin.autodiscover()

import api.views

urlpatterns = [
    path("interactions", api.views.interactions, name="interactions"),
    path("gene_words", api.views.gene_words, name="gene_words"),
    path(
        "",
        RedirectView.as_view(url='static/index.html', permanent=False),
        name='index')
]
