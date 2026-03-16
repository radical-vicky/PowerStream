import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = 'Generates video sitemap files'

    def handle(self, *args, **options):
        self.stdout.write('Generating video sitemaps...')
        
        # Generate sitemap files in static directory
        output_dir = os.path.join(settings.BASE_DIR, 'static', 'sitemaps')
        os.makedirs(output_dir, exist_ok=True)
        
        # Use Django's sitemap generator
        call_command('generate_sitemap', output_dir=output_dir)
        
        self.stdout.write(self.style.SUCCESS('Sitemaps generated successfully!'))