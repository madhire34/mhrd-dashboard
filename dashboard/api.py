from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django.utils.text import slugify

from .models import State, Scheme, Initiative
from .serializers import StateSerializer, SchemeSerializer, InitiativeSerializer

class StateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = State.objects.all().order_by('name')
    serializer_class = StateSerializer
    permission_classes = [AllowAny]

class SchemeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Scheme.objects.all().order_by('name')
    serializer_class = SchemeSerializer
    permission_classes = [AllowAny]

class InitiativeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InitiativeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Initiative.objects.select_related('state', 'scheme').all()
        year = self.request.query_params.get('year')
        state = self.request.query_params.get('state')
        scheme = self.request.query_params.get('scheme')
        category = self.request.query_params.get('category')
        if year:
            try:
                qs = qs.filter(year=int(year))
            except ValueError:
                pass
        if state:
            qs = qs.filter(state__name=state) | qs.filter(state__slug=slugify(state))
        if scheme:
            qs = qs.filter(scheme__name=scheme) | qs.filter(scheme__slug=slugify(scheme))
        if category:
            qs = qs.filter(category=category)
        return qs.order_by('-year', 'state__name')
