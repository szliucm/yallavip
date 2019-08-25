import re
from django.utils.timezone import now
from datetime import timedelta
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import FbConversation
from customer.serializers import CustomerCartListSerializer,CustomerFavListSerializer, CustomerFavSerializer


class FbConversationSerializer(serializers.ModelSerializer):
    cart = CustomerCartListSerializer(many=True)
    fav = CustomerFavListSerializer(many=True)


    class Meta:
        model = FbConversation
        #fields = ('id', 'conversation_no','customer','cart', 'fav')
        fields = "__all__"
