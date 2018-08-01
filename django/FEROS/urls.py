from django.conf.urls import url

from . import views

app_name = "FEROS"

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^raw/$', views.raw, name='raw'),
    url(r'^reduced/$', views.reduced, name='reduced'),
    url(r'^longtermcal/$', views.longtermcal, name='longtermcal'),
    url(r'^longtermrv/$', views.longtermrv, name='longtermrv'),
    url(r'^help/$', views.help, name='help'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^wavesol/$', views.wavesol, name='wavesol'),
    url(r'^plotcal/$', views.plotcal, name='plotcal'),
    url(r'^spectra/$', views.spectra, name='spectra'),
]
