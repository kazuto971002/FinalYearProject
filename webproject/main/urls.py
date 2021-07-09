from django.conf.urls import url
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^add_user', views.addUser),
    url(r'^save_user', views.saveUser),
    url(r'^check_users', views.checkUsers),

    path('del_user/', views.delUser, name='del_user'),

    url(r'^success$', views.success),

    url(r'^add_known_person', views.addKnownPerson),
    url(r'^save_known_person', views.saveKnownPerson),
    path('view_known_persons/', views.viewKnownPerson, name='view_known_persons'),
    path('del_known_persons/<slug:person_id>/', views.delPerson, name='del_person'),

    path('detected/', views.detected, name='detected'),
    path('video_stream/', views.video_stream, name='video_stream'),
    path('video_feed/', views.video_feed, name='video_feed'),

    url(r'^login$', views.login),
    url(r'^loginpage', views.login_view),
    url(r'^logout', views.logout_view),
    url(r'^detectImage', views.detectImage),
]

if settings.DEBUG:
    #urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
