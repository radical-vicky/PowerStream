// Like functionality
function likeVideo(videoId) {
    fetch(`/videos/${videoId}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const likeCount = document.getElementById('like-count');
            const likeBtn = document.getElementById('like-btn');
            
            likeCount.textContent = data.likes_count;
            
            if (data.liked) {
                likeBtn.classList.add('text-danger');
                likeBtn.classList.remove('text-muted');
            } else {
                likeBtn.classList.remove('text-danger');
                likeBtn.classList.add('text-muted');
            }
        }
    });
}

// Comment functionality
function submitComment(videoId, parentId = null) {
    const form = parentId ? document.getElementById(`reply-form-${parentId}`) : document.getElementById('comment-form');
    const content = parentId ? form.querySelector('textarea[name="content"]').value : form.querySelector('input[name="content"]').value;
    
    fetch(`/videos/${videoId}/comment/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            content: content,
            parent_id: parentId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Simple solution - reload to show new comment
        }
    });
}

// Share functionality
function shareVideo(videoId, platform) {
    const videoUrl = window.location.origin + '/videos/' + videoId + '/';
    let shareUrl = '';
    
    switch(platform) {
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(videoUrl)}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(videoUrl)}`;
            break;
        case 'whatsapp':
            shareUrl = `https://wa.me/?text=${encodeURIComponent(videoUrl)}`;
            break;
        case 'copy':
            navigator.clipboard.writeText(videoUrl).then(() => {
                alert('Link copied to clipboard!');
            });
            return;
    }
    
    if (shareUrl) {
        window.open(shareUrl, '_blank', 'width=600,height=400');
    }
    
    // Track share
    fetch(`/videos/${videoId}/share/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ platform: platform })
    });
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Video player
function initializeVideoPlayer() {
    const video = document.querySelector('video');
    if (video) {
        video.addEventListener('play', function() {
            // Track view (handled by hitcount)
        });
        
        video.addEventListener('ended', function() {
            // Show related videos or next video
            console.log('Video ended');
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeVideoPlayer();
    
    // Like button handler
    const likeBtn = document.getElementById('like-btn');
    if (likeBtn) {
        likeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const videoId = this.dataset.videoId;
            likeVideo(videoId);
        });
    }
    
    // Share buttons
    document.querySelectorAll('[data-share]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const videoId = this.dataset.videoId;
            const platform = this.dataset.platform;
            shareVideo(videoId, platform);
        });
    });
    
    // Reply buttons
    document.querySelectorAll('.reply-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const commentId = this.dataset.commentId;
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            replyForm.classList.toggle('d-none');
        });
    });
});