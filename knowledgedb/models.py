from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Least, Greatest
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class Divisions(models.TextChoices):
    COED = "coed", _("Coed")
    OPEN = "open", _("Open")
    WOMEN = "women", _("Women")


class Nation(models.Model):
    """
    ISO-based nation/country entity.
    Keep it small and canonical so you can safely FK to it everywhere.
    """
    name = models.CharField(max_length=100)
    short = models.CharField(max_length=3, unique=True)   # e.g., "DEU"
    flag_emoji = models.CharField(max_length=8, blank=True) # "🇩🇪" etc.

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="ck_nation_short_upper",
                check=Q(short__regex=r"^[A-Z]{3}$"),
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.short})"


class Player(models.Model):
    firstname = models.CharField(max_length=120)
    lastname = models.CharField(max_length=120)
    birthdate = models.DateField(null=True, blank=True)
    playing_since = models.DateField(null=True, blank=True)
    eura_pro = models.BooleanField()
    hometeam = models.CharField(max_length=120, blank=True)
    speciality = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    normal_teammate = models.ManyToManyField("self", null=True, blank=True)

    class Meta:
        constraints = [
            # Tweak uniqueness as needed for your data quality
            models.UniqueConstraint(
                fields=["firstname", "lastname", "birthdate"],
                name="uq_player_name_dob",
                deferrable=models.Deferrable.DEFERRED,
            )
        ]
        indexes = [
            models.Index(fields=["lastname", "firstname"]),
        ]

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class Team(models.Model):
    playerA = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="teams_as_playerA"
    )
    playerB = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="teams_as_playerB"
    )
    division = models.CharField(max_length=5, choices=Divisions)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(playerA=models.F("playerB")),
                name="ck_team_two_distinct_players",
            ),
            # NOTE: no deferrable here — expressions can't be deferred
            models.UniqueConstraint(
                models.functions.Least("playerA", "playerB"),
                models.functions.Greatest("playerA", "playerB"),
                name="uq_team_player_pair_unordered",
            ),
        ]
        indexes = [
            models.Index(
                models.functions.Least("playerA", "playerB"),
                models.functions.Greatest("playerA", "playerB"),
                name="idx_team_pair_unordered",
            ),
        ]

    def __str__(self):
        return f"{self.playerA.lastname}/{self.playerB.lastname}"


class Tournament(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    division = models.CharField(max_length=5, choices=Divisions)

    class Meta:
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["division", "start_date"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_division_display()})"


class Squad(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="squads"
    )
    nation = models.ForeignKey(
        "Nation",
        on_delete=models.PROTECT,              # avoid orphaning squads if a nation is removed
        related_name="squads",
    )
    instagram = models.URLField(null=True, blank=True)

    # Convenience many-to-many (through table holds seed/order)
    teams = models.ManyToManyField(
        Team, through="SquadTeam", related_name="squads", blank=True
    )
    class Meta:
        constraints = [
            # Optional: uncomment if you want at most one squad per nation per tournament.
            models.UniqueConstraint(
                fields=["tournament", "nation"],
                name="uq_squad_unique_nation_per_tournament",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]
        indexes = [
            models.Index(fields=["tournament", "nation"]),  # helpful for filters/views
        ]

    def __str__(self):
        return f"{self.tournament}: {self.nation} ({self.tournament.get_division_display()})"


class SquadTeam(models.Model):
    """
    Places a team into a squad at a unique seed (1..n).
    Keep business rule "each squad has 3..5 teams" in app logic or a DB trigger.
    """
    squad = models.ForeignKey(Squad, on_delete=models.CASCADE, related_name="squad_teams")
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, related_name="squad_teams")
    seed = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = (
            ("squad", "team"),   # a team can appear at most once in a squad
        )
        constraints = [
            models.UniqueConstraint(
                fields=["squad", "seed"],
                name="uq_squad_seed_unique",
                deferrable=models.Deferrable.DEFERRED,
            ),
        ]
        indexes = [
            models.Index(fields=["team"]),
            models.Index(fields=["squad", "seed"]),
        ]

    def __str__(self):
        return f"{self.squad} • {self.team} (seed {self.seed})"
