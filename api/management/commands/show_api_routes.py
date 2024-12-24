from django.core.management.base import BaseCommand
from django.urls import get_resolver
from rest_framework.routers import DefaultRouter

class Command(BaseCommand):
    help = 'Shows all API routes with their HTTP methods'

    def handle(self, *args, **options):
        from api.urls import router  # Import the router from your urls.py
        
        self.stdout.write(self.style.HTTP_INFO('\nAPI Routes:'))
        self.stdout.write(self.style.HTTP_INFO('='*80))
        
        for prefix, viewset, basename in router.registry:
            self.stdout.write(self.style.HTTP_INFO(f'\n{prefix}:'))
            
            # Get viewset class
            viewset_class = viewset
            if not isinstance(viewset, type):
                viewset_class = viewset.__class__
            
            # Get extra actions
            extra_actions = getattr(viewset_class, 'get_extra_actions', lambda: [])()
            for action in extra_actions:
                http_methods = getattr(action, 'bind_to_methods', ['GET'])
                method_name = action.__name__
                self.stdout.write(f"  {', '.join(http_methods)} /{prefix}/{method_name}/")
            
            # Check for standard actions
            if hasattr(viewset_class, 'list'):
                self.stdout.write(f"  GET /{prefix}/")
            if hasattr(viewset_class, 'create'):
                self.stdout.write(f"  POST /{prefix}/")
            if hasattr(viewset_class, 'retrieve'):
                self.stdout.write(f"  GET /{prefix}/<id>/")
            if hasattr(viewset_class, 'update'):
                self.stdout.write(f"  PUT /{prefix}/<id>/")
            if hasattr(viewset_class, 'partial_update'):
                self.stdout.write(f"  PATCH /{prefix}/<id>/")
            if hasattr(viewset_class, 'destroy'):
                self.stdout.write(f"  DELETE /{prefix}/<id>/") 