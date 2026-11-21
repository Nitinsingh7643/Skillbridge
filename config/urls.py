from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('student/', include('students.urls')),
    path('colleges/', include('colleges.urls')),
    path('recruiters/', include('recruiters.urls')),
    path('skills/', include('skills.urls')),
    path('collaboration/', include('collaboration.urls')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
