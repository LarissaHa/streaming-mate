from django.urls import path
from . import views

urlpatterns = [
    path('', views.nationalities, name='nationalities'),
    path('nation/<str:short>/', views.nation_detail, name='nation_detail'),
    path('', views.tournaments, name='tournaments'),
    path('', views.players, name='players'),
    # teams filtered by tournament (and division)
    # players filtered by nationality
    # squads filtert by tournament and division
    # matchups ?
]