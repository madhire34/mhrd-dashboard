from rest_framework import serializers
from .models import State, Scheme, Initiative

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name", "slug", "lat", "lng"]

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ["id", "name", "slug"]

class InitiativeSerializer(serializers.ModelSerializer):
    state = StateSerializer()
    scheme = SchemeSerializer()

    class Meta:
        model = Initiative
        fields = [
            "id", "name", "state", "scheme", "category", "year", "status",
            "progress", "schools_impacted", "students_impacted", "scholarships_awarded", "budget_utilized"
        ]
