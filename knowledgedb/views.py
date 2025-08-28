from django.shortcuts import render
from django.http import Http404
from django.db.models import Q, Prefetch, F
from .models import Divisions, Nation, Tournament, Player, Squad, SquadTeam, Team
from django.shortcuts import render, get_object_or_404

def nations(request):
    nations = Nation.objects.order_by('name')
    return render(request, 'knowledgedb/nations.html', {'nations': nations})

def nations_detail(request, short):
    nation = get_object_or_404(Nation, short=short)
    squads = (
        Squad.objects
        .filter(nation=nation)
        .select_related("tournament", "nation")
        .prefetch_related(
            Prefetch(
                "squad_teams",
                queryset=SquadTeam.objects
                    .select_related("team", "team__playerA", "team__playerB")
                    .order_by("seed"),
            )
        )
    )

    # Base queryset of teams that actually appear in this nation's squads
    teams_in_nation_qs = (
        Team.objects
        .filter(squad_teams__squad__nation=nation)
        .select_related("playerA", "playerB")
        .distinct()
    )

    # Players who appear in those teams (as you had), with prefetched teams
    players = (
        Player.objects
        .filter(
            Q(teams_as_playerA__squad_teams__squad__nation=nation) |
            Q(teams_as_playerB__squad_teams__squad__nation=nation)
        )
        .distinct()
        .order_by("lastname", "firstname")
        .prefetch_related(
            Prefetch("teams_as_playerA", queryset=teams_in_nation_qs, to_attr="teams_as_A_in_nation"),
            Prefetch("teams_as_playerB", queryset=teams_in_nation_qs, to_attr="teams_as_B_in_nation"),
        )
    )

    # Combine A/B teams into a single attribute per player (deduped, order preserved)
    players = list(players)  # evaluate so we can attach attributes
    for p in players:
        combined = []
        seen = set()
        for t in getattr(p, "teams_as_A_in_nation", []):
            if t.pk not in seen:
                combined.append(t); seen.add(t.pk)
        for t in getattr(p, "teams_as_B_in_nation", []):
            if t.pk not in seen:
                combined.append(t); seen.add(t.pk)
        p.teams_in_nation = combined  # <- use this in the template

    return render(
        request,
        "knowledgedb/nations_detail.html",
        {"nation": nation, "players": players, "squads": squads},
    )

def start(request):
    tournaments = Tournament.objects.order_by("name")
    return render(request, 'knowledgedb/start.html', {'tournaments': tournaments})

def divisions_detail(request, division_slug: str):
    division = division_slug.lower()
    if division not in Divisions.values:
        raise Http404("Unknown division")
    squads = (
        Squad.objects
        .filter(tournament__division=division)
        .select_related("tournament", "nation")
        .prefetch_related(
            Prefetch(
                "squad_teams",
                queryset=SquadTeam.objects
                    .select_related("team", "team__playerA", "team__playerB")
                    .order_by("seed"),
            )
        )
        .order_by("tournament__start_date")
    )
    return render(
        request,
        "knowledgedb/divisions_detail.html", {"division": division, "squads": squads},
    )

def squads_detail(request, id):
    squad = get_object_or_404(Squad, id=id)
    teams = (
        Team.objects
        .filter(squad_teams__squad=squad)
        .annotate(seed=F("squad_teams__seed"))
        .select_related("playerA", "playerB")
        .prefetch_related("playerA__normal_teammate", "playerB__normal_teammate")
        .order_by("seed")
    )
    return render(request, 'knowledgedb/squads_detail.html', {"squad": squad, "teams": teams})

def tournaments(request):
    return render(request, 'knowledgedb/tournaments.html', {})

def players(request):
    return render(request, 'knowledgedb/players.html', {})