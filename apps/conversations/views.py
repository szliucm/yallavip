from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from .serializers import FbConversationSerializer
from .models import FbConversation
# Create your views here.


class FbConversationViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    retrieve:
        显示聊天记录详情
    """

    serializer_class = FbConversationSerializer
    queryset = FbConversation.objects.all().order_by('id')
