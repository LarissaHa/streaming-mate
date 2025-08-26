from django.shortcuts import render
from django.db.models import Q
from .models import Nation, Tournament, Player, Squad, SquadTeam, Team
from django.shortcuts import render, get_object_or_404

def nationalities(request):
    nations = Nation.objects.order_by('name')
    return render(request, 'knowledgedb/nationalities.html', {'nations': nations})

def nation_detail(request, short):
    nation = get_object_or_404(Nation, short=short)
    teams = (
            Team.objects
            .filter(squad_teams__squad__nation=nation)
            .select_related('playerA', 'playerB')
            .prefetch_related('squad_teams__squad')
            .distinct()
        )

    players = (
            Player.objects
            .filter(Q(teams_as_playerA__in=teams) | Q(teams_as_playerB__in=teams))
            .distinct()
            .order_by('lastname', 'firstname')
        )
    return render(request, 'knowledgedb/nation_detail.html', {'nation': nation, 'players': players, 'teams': teams})

def tournaments(request):
    return render(request, 'knowledgedb/tournaments.html', {})

def players(request):
    return render(request, 'knowledgedb/players.html', {})