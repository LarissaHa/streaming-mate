from django import forms
from .models import Squad

class SquadMatchForm(forms.Form):
    squad1 = forms.ModelChoiceField(
        label="Squad A",
        queryset=Squad.objects.select_related("tournament", "nation").order_by("tournament__start_date"),
    )
    squad2 = forms.ModelChoiceField(
        label="Squad B",
        queryset=Squad.objects.select_related("tournament", "nation").order_by("tournament__start_date"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def fmt(s):
            # shows “Coed — Germany”
            return f"{s.tournament.get_division_display()} — {s.nation.name}"
            # optional fancier version with tournament/date:
            # return f"{s.tournament.get_division_display()} — {s.nation.name} ({s.tournament.name})"

        self.fields["squad1"].label_from_instance = fmt
        self.fields["squad2"].label_from_instance = fmt

    def clean(self):
        cleaned = super().clean()
        s1 = cleaned.get("squad1")
        s2 = cleaned.get("squad2")
        if s1 and s2:
            if s1 == s2:
                self.add_error("squad2", "Pick two different squads.")
            # Optional: require same division
            if s1.tournament.division != s2.tournament.division:
                self.add_error(None, "Both squads must be in the same division.")
        return cleaned