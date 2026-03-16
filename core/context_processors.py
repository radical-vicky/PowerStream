from .models import Background
import logging
import os

logger = logging.getLogger(__name__)

def background_processor(request):
    """
    Context processor to add active background to all templates
    """
    context = {
        'active_background': None,
        'background_image_url': None,
        'background_video_url': None,
        'background_color': '#212031',
        'video_exists': False,
        'video_url_debug': None,
    }
    
    try:
        # Get the active background
        active_background = Background.objects.filter(is_active=True).first()
        
        if active_background:
            logger.info(f"Found active background: {active_background.name} (type: {active_background.bg_type})")
            context['active_background'] = active_background
            
            # Add specific context based on background type
            if active_background.bg_type == 'image' and active_background.image:
                context['background_image_url'] = active_background.image.url
                logger.info(f"Image URL: {active_background.image.url}")
                logger.info(f"Image path: {active_background.image.path}")
                
            elif active_background.bg_type == 'video' and active_background.video:
                # Check if video file exists
                video_path = active_background.video.path
                video_exists = os.path.exists(video_path)
                
                context['background_video_url'] = active_background.video.url
                context['video_exists'] = video_exists
                context['video_url_debug'] = active_background.video.url
                
                logger.info(f"Video URL: {active_background.video.url}")
                logger.info(f"Video path: {video_path}")
                logger.info(f"Video file exists: {video_exists}")
                
                # Log file info
                if video_exists:
                    file_size = os.path.getsize(video_path)
                    logger.info(f"Video file size: {file_size} bytes")
                
            elif active_background.bg_type == 'color' and active_background.color:
                context['background_color'] = active_background.color
                
    except Exception as e:
        logger.error(f"Error in background_processor: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return context