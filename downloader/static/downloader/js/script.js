document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const downloadForm = document.getElementById('download-form');
    const youtubeUrl = document.getElementById('youtube-url');
    const previewButton = document.getElementById('preview-button');
    const downloadButton = document.getElementById('download-button');
    const previewContainer = document.getElementById('preview-container');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoTitle = document.getElementById('video-title');
    const downloadInfo = document.getElementById('download-info');
    const urlError = document.getElementById('url-error');
    const loadingElement = document.getElementById('loading');
    const formatChoices = document.querySelectorAll('input[name="format_choice"]');
    const qualitySelect = document.getElementById('id_quality');
    
    // Ensure loading is hidden on initial page load
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
    
    // Regular expression for YouTube URL validation
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})(.*)$/;
    
    // Event listener for URL input to validate
    youtubeUrl.addEventListener('input', validateUrl);
    
    // Event listener for preview button
    previewButton.addEventListener('click', previewVideo);
    
    // Event listener for format change
    formatChoices.forEach(choice => {
        choice.addEventListener('change', updateQualityOptions);
    });
    
    // Initialize quality options based on default format
    updateQualityOptions();
    
    // URL Validation function
    function validateUrl() {
        const url = youtubeUrl.value.trim();
        const isValid = youtubeRegex.test(url);
        
        if (url === '') {
            urlError.textContent = '';
            previewButton.disabled = true;
            return false;
        } else if (!isValid) {
            urlError.textContent = 'URL không hợp lệ. Vui lòng nhập URL YouTube hợp lệ.';
            previewButton.disabled = true;
            return false;
        } else {
            urlError.textContent = '';
            previewButton.disabled = false;
            return true;
        }
    }
    
    // Function to update quality options based on format choice
    function updateQualityOptions() {
        const formatChoice = document.querySelector('input[name="format_choice"]:checked').value;
        
        // Clear existing options
        qualitySelect.innerHTML = '';
        
        if (formatChoice === 'mp3') {
            // Audio quality options
            addOption(qualitySelect, 'highest', 'Cao nhất');
            addOption(qualitySelect, 'medium', 'Trung bình');
            addOption(qualitySelect, 'lowest', 'Thấp nhất');
        } else {
            // Video quality options
            addOption(qualitySelect, 'highest', 'HD/Cao nhất');
            addOption(qualitySelect, 'medium', 'Trung bình (720p)');
            addOption(qualitySelect, 'lowest', 'Thấp (480p)');
        }
    }
    
    // Helper function to add options to select element
    function addOption(selectElement, value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        selectElement.appendChild(option);
    }
    
    // Function to get video ID from YouTube URL
    function getVideoId(url) {
        const match = url.match(youtubeRegex);
        return match ? match[4] : null;
    }
    
    // Function to preview video
    function previewVideo(e) {
        e.preventDefault();
        
        if (!validateUrl()) {
            return;
        }
        
        const url = youtubeUrl.value.trim();
        const videoId = getVideoId(url);
        const formatChoice = document.querySelector('input[name="format_choice"]:checked').value;
        const quality = qualitySelect.value;
        
        if (!videoId) {
            urlError.textContent = 'Không thể xác định ID video YouTube.';
            return;
        }
        
        // Show loading indicator
        loadingElement.classList.remove('hidden');
        previewContainer.classList.add('hidden');
        downloadButton.disabled = true;
        
        // Get the CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Fetch video info from server
        fetch('/get_video_info/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({
                'url': url,
                'format_choice': formatChoice,
                'quality': quality
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Có lỗi xảy ra khi lấy thông tin video');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            loadingElement.classList.add('hidden');
            
            // Display video info
            videoThumbnail.src = `https://img.youtube.com/vi/${data.videoId}/mqdefault.jpg`;
            videoTitle.textContent = data.title;
            
            const formatLabel = formatChoice === 'mp4' ? 'Video MP4' : 'Audio MP3';
            const qualityLabel = quality === 'highest' ? 'chất lượng cao' : 
                               quality === 'medium' ? 'chất lượng trung bình' : 'chất lượng thấp';
            
            downloadInfo.textContent = `${formatLabel} - ${qualityLabel}`;
            
            // Show preview and enable download button
            previewContainer.classList.remove('hidden');
            downloadButton.disabled = false;
        })
        .catch(error => {
            // Hide loading indicator and show error
            loadingElement.classList.add('hidden');
            urlError.textContent = error.message;
        });
    }
    
    // Handle form submission for download
    downloadForm.addEventListener('submit', function(event) {
        if (!validateUrl()) {
            event.preventDefault();
            return false;
        }
        
        // Show loading during submission
        loadingElement.classList.remove('hidden');
        downloadButton.disabled = true;
        previewButton.disabled = true;
    });
});
