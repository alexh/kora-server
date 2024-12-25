from django.core.management.base import BaseCommand
from django.urls import get_resolver
from rest_framework.routers import SimpleRouter, DefaultRouter

class Command(BaseCommand):
    help = 'Shows all API routes in the application'

    def handle(self, *args, **options):
        resolver = get_resolver()
        
        def format_pattern(pattern):
            # Clean up the pattern string
            path = str(pattern.pattern)
            # Remove regex start/end markers
            path = path.replace('^', '').replace('$', '')
            # Convert regex patterns to more readable format
            path = path.replace('(?P<pk>[^/.]+)', '{id}')
            path = path.replace('(?P<format>[a-z0-9]+)', 'json')
            # Remove format suffix patterns
            path = path.replace('.json/?', '')
            return path

        def process_url_patterns(patterns, prefix=''):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is a URLResolver
                    new_prefix = prefix + format_pattern(pattern)
                    process_url_patterns(pattern.url_patterns, new_prefix)
                else:
                    # This is a URLPattern
                    path = prefix + format_pattern(pattern)
                    
                    # Skip if not an API route or if it's a format suffix route
                    if not path.startswith('api/') or '.json' in path or path == 'api/':
                        continue
                    
                    view = pattern.callback
                    if hasattr(view, 'cls'):
                        view_name = view.cls.__name__
                        
                        # Get HTTP methods
                        methods = []
                        if hasattr(view.cls, 'get'):
                            methods.append('GET')
                        if hasattr(view.cls, 'post'):
                            methods.append('POST')
                        if hasattr(view.cls, 'put'):
                            methods.append('PUT')
                        if hasattr(view.cls, 'patch'):
                            methods.append('PATCH')
                        if hasattr(view.cls, 'delete'):
                            methods.append('DELETE')
                        
                        methods_str = ', '.join(methods) if methods else 'ALL'
                        self.stdout.write(f"{path:<50} {view_name:<30} {methods_str}")

        self.stdout.write("\nAPI Routes:")
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'Path':<50} {'View':<30} {'Methods'}")
        self.stdout.write("-" * 80)
        
        process_url_patterns(resolver.url_patterns) 