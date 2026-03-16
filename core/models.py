from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Background(models.Model):
    BG_TYPES = (
        ('color', 'Solid Color'),
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    name = models.CharField(max_length=100)
    bg_type = models.CharField(max_length=10, choices=BG_TYPES, default='color')
    
    # For color backgrounds
    color = models.CharField(max_length=20, blank=True, null=True, help_text="Hex color code, e.g., #0a0a0a")
    
    # For image backgrounds
    image = models.ImageField(upload_to='backgrounds/images/', blank=True, null=True)
    
    # For video backgrounds
    video = models.FileField(upload_to='backgrounds/videos/', blank=True, null=True)
    
    # Customization options
    card_bg_color = models.CharField(max_length=20, default='#111111', help_text="Card background color")
    hover_bg_color = models.CharField(max_length=20, default='#1a1a1a', help_text="Hover background color")
    text_color = models.CharField(max_length=20, default='#ffffff', help_text="Primary text color")
    text_secondary_color = models.CharField(max_length=20, default='#a0a0a0', help_text="Secondary text color")
    border_color = models.CharField(max_length=20, default='#2a2a2a', help_text="Border color")
    accent_color = models.CharField(max_length=20, default='#3b82f6', help_text="Accent color")
    accent_hover_color = models.CharField(max_length=20, default='#2563eb', help_text="Accent hover color")
    
    # Overlay settings
    overlay_opacity = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Overlay opacity (0.0 - 1.0)"
    )
    
    # Navbar settings
    navbar_opacity = models.FloatField(
        default=0.95,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Navbar opacity (0.0 - 1.0)"
    )
    
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def get_navbar_rgba(self):
        """Convert hex color to rgba with navbar opacity"""
        if self.bg_type == 'color' and self.color:
            # Convert hex to rgb
            hex_color = self.color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {self.navbar_opacity})"
        return f"rgba(17, 17, 17, {self.navbar_opacity})"
    
    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other backgrounds
            Background.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)