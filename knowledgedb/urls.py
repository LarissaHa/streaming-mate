from django.urls import path
from . import views

urlpatterns = [
    path('', views.start, name='start'),
    path('divisions/<str:division_slug>/', views.divisions_detail, name='divisions_detail'),
    path('nations/', views.nations, name='nations'),
    path('nations/<str:short>/', views.nations_detail, name='nations_detail'),
    path('squads/<int:id>', views.squads_detail, name='squads_detail'),
    path('squads/match/', views.squad_match_view, name='squad-match'),
    # path('', views.players, name='players'),
    # teams filtered by tournament (and division)
    # players filtered by nationality
    # squads filtert by tournament and division
    # matchups ?
]