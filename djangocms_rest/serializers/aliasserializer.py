from rest_framework import serializers
from cms.models import PageUrl


class AliasSerializer(serializers.Serializer):
    url = serializers.CharField()
    redirect_to = serializers.CharField()
    language = serializers.CharField()
    is_active = serializers.BooleanField()

    def to_representation(self, instance):
        return {
            'url': instance.path,
            'redirect_to': instance.page.get_absolute_url(instance.language),
            'language': instance.language,
            'is_active': instance.page.is_published(instance.language)
        }
