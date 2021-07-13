from django.http import JsonResponse


class JSONResponseMixin:
    """A mixin that can be used to render a JSON response."""

    def render_to_json_response(self, context, **response_kwargs):
        """Return a JSON response, transforming 'context' to make the payload."""
        return JsonResponse(self.get_data(context), safe=False, **response_kwargs)

    def get_data(self, context):
        """Return an object that will be serialized as JSON by json.dumps()."""
        return context
