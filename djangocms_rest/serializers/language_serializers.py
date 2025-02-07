from rest_framework import serializers


class LanguageSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)
    name = serializers.CharField(max_length=100)
    public = serializers.BooleanField()
    fallbacks = serializers.ListField(
        child=serializers.CharField(max_length=10),
        allow_empty=True
    )
    redirect_on_fallback = serializers.BooleanField()
    hide_untranslated = serializers.BooleanField()
    pages = serializers.URLField()
