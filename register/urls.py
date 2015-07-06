from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r"^login/$", views.login, name="account_login"),
    url(r'^signup/', views.signup, name='account_signup'),
    url(r'^', include('allauth.urls')),
]