from django.conf.urls import re_path

from . import views

app_name = "FEROS"

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^raw/$', views.raw, name='raw'),
    re_path(r'^reduced/$', views.reduced, name='reduced'),
    re_path(r'^longtermcal/$', views.longtermcal, name='longtermcal'),
    re_path(r'^longtermrv/$', views.longtermrv, name='longtermrv'),
    re_path(r'^help/$', views.help, name='help'),
    re_path(r'^contact/$', views.contact, name='contact'),
    re_path(r'^wavesol/$', views.wavesol, name='wavesol'),
    re_path(r'^plotcal/$', views.plotcal, name='plotcal'),
    re_path(r'^spectra/$', views.spectra, name='spectra'),
]
