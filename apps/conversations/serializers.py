import re
from django.utils.timezone import now
from datetime import timedelta
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import FbConversation


class FbConversationSerializer(serializers.ModelSerializer):

    class Meta:
        model = FbConversation
        fields = ('pk', 'conversation_no','customer')

