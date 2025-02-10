from typing import Any, Dict, Optional

from cms.models import CMSPlugin
from cms.plugin_rendering import ContentRenderer
from rest_framework import serializers
from sekizai.context import SekizaiContext
from sekizai.helpers import get_varname


def render_plugin(instance: CMSPlugin, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    instance, plugin = instance.get_plugin_instance()
    if not instance:
        return None

    class PluginSerializer(serializers.ModelSerializer):
        class Meta:
            model = instance.__class__
            exclude = (
                "id",
                "placeholder",
                "language",
                "position",
                "creation_date",
                "changed_date",
                "parent",
            )

    json = PluginSerializer(instance, context=context).data
    return json


def render_html(request, placeholder, language):
    content_renderer = ContentRenderer(request)
    context = SekizaiContext({"request": request, "LANGUAGE_CODE": language})
    content = content_renderer.render_placeholder(
        placeholder,
        context=context,
        language=language,
        use_cache=False,
    )
    sekizai_blocks = context[get_varname()]

    return {
        "html": content,
        **{key: "".join(value) for key, value in sekizai_blocks.items() if value},
    }
