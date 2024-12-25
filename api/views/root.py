from django.http import JsonResponse
from config.version import VERSION

def welcome(request):
    return JsonResponse({
        "message": f"welcome to UMI-OS v{VERSION}"
    }) 