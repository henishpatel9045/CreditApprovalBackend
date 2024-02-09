from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin

from core.models import Customer
from core.serializers import CustomerSerializer


class CustomerRegisterViewSet(CreateModelMixin, GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
