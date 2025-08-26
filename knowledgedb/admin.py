from django.contrib import admin
from .models import Player, Team, Squad, SquadTeam, Tournament, Nation

admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Squad)
admin.site.register(SquadTeam)
admin.site.register(Tournament)
admin.site.register(Nation)