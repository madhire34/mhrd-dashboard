from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from dashboard.data import INITIATIVES, STATE_COORDINATES, SCHEMES
from dashboard.models import State, Scheme, Initiative

class Command(BaseCommand):
    help = "Import demo initiatives from in-memory data into the database"

    def handle(self, *args, **options):
        # States
        state_objs = {}
        for name, coords in STATE_COORDINATES.items():
            state, _ = State.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name), "lat": coords.get("lat"), "lng": coords.get("lng")},
            )
            if state.lat is None and name in STATE_COORDINATES:
                state.lat = STATE_COORDINATES[name]["lat"]
                state.lng = STATE_COORDINATES[name]["lng"]
                state.save(update_fields=["lat", "lng"])
            state_objs[name] = state
        
        # Schemes
        scheme_objs = {}
        for name in set(SCHEMES):
            scheme, _ = Scheme.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
            scheme_objs[name] = scheme
        
        # Initiatives
        created = 0
        for row in INITIATIVES:
            state = state_objs.get(str(row["state"]))
            scheme = scheme_objs.get(str(row["scheme"]))
            if not state or not scheme:
                continue
            obj, was_created = Initiative.objects.get_or_create(
                name=row["name"],
                state=state,
                scheme=scheme,
                year=int(row["year"]),
                defaults={
                    "category": str(row["category"]),
                    "status": str(row["status"]),
                    "progress": float(row["progress"]),
                    "schools_impacted": int(row["schools_impacted"]),
                    "students_impacted": int(row["students_impacted"]),
                    "scholarships_awarded": int(row["scholarships_awarded"]),
                    "budget_utilized": float(row["budget_utilized"]),
                },
            )
            created += 1 if was_created else 0
        
        self.stdout.write(self.style.SUCCESS(f"Imported demo data. New initiatives: {created}"))
