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
    const loadingText = document.getElementById('loading-text');
    const progressBar = document.getElementById('progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    const formatChoices = document.querySelectorAll('input[name="format_choice"]');
    const qualitySelect = document.getElementById('id_quality');
    
    // Variables for progress tracking
    let downloadId = null;
    let progressInterval = null;
    
    // Ensure loading is hidden on initial page load
    if (loadingElement) {
        loadingElement.classList.add('hidden');
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
        
        // Show loading indicator with progress
        loadingElement.classList.remove('hidden');
        previewContainer.classList.add('hidden');
        downloadButton.disabled = true;
        
        // Reset progress bar
        updateProgress(5, 'Đang kết nối đến YouTube...');
        
        // Simulate progress for preview operation
        let previewProgress = 5;
        const previewInterval = setInterval(() => {
            previewProgress += Math.floor(Math.random() * 5) + 1;
            if (previewProgress > 90) {
                previewProgress = 90; // Cap at 90% for fetch operation
                clearInterval(previewInterval);
            }
            updateProgress(previewProgress, 'Đang lấy thông tin video...');
        }, 300);
        
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
            // Update to 100% when fetch completes successfully
            updateProgress(100, 'Hoàn thành!');
            
            // Use setTimeout to show the 100% briefly before hiding
            setTimeout(() => {
                // Hide loading indicator - make sure it's hidden
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
                previewButton.disabled = false;
                
                // Clear any running intervals
                clearAllIntervals();
            }, 800);
        })
        .catch(error => {
            // Update progress to show error
            updateProgress(100, 'Đã xảy ra lỗi');
            
            // Use setTimeout to show the error state briefly
            setTimeout(() => {
                // Hide loading indicator and show error
                loadingElement.classList.add('hidden');
                urlError.textContent = error.message;
                
                // Clear any running intervals
                clearAllIntervals();
            }, 500);
        });
    }
    
    // Handle form submission for download
    downloadForm.addEventListener('submit', function(event) {
        // Prevent the default form submission - important to stop page reloading
        event.preventDefault();
        
        if (!validateUrl()) {
            return false;
        }
        
        // Generate a random downloadId to track this download
        downloadId = Math.random().toString(36).substring(2, 15);
        
        // Show loading during submission
        loadingElement.classList.remove('hidden');
        previewContainer.classList.add('hidden');
        downloadButton.disabled = true;
        previewButton.disabled = true;
        
        // Reset and start with initial progress
        updateProgress(5, 'Bắt đầu tải xuống...');
        
        // Get form data
        const formData = new FormData(downloadForm);
        formData.append('download_id', downloadId);
        
        // Get the CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Start progress tracking
        startProgressTracking();
        
        // Create an iframe to handle the file download without page reload
        let downloadFrame = document.getElementById('download-frame');
        if (!downloadFrame) {
            downloadFrame = document.createElement('iframe');
            downloadFrame.id = 'download-frame';
            downloadFrame.name = 'download-frame';
            downloadFrame.style.display = 'none';
            document.body.appendChild(downloadFrame);
        }
        
        // Add iframe to body and create a form to submit to it
        const downloadFormTemp = document.createElement('form');
        downloadFormTemp.method = 'POST';
        downloadFormTemp.action = downloadForm.action;
        downloadFormTemp.target = 'download-frame';
        
        // Add all form fields
        for (const pair of formData.entries()) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = pair[0];
            input.value = pair[1];
            downloadFormTemp.appendChild(input);
        }
        
        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;
        downloadFormTemp.appendChild(csrfInput);
        
        // Submit the form through the iframe to avoid page reload
        document.body.appendChild(downloadFormTemp);
        downloadFormTemp.submit();
        document.body.removeChild(downloadFormTemp);
        
        // Set a backup timer to hide loading and reset UI after 60 seconds
        // This ensures loading disappears even if progress tracking fails
        setTimeout(() => {
            loadingElement.classList.add('hidden');
            previewButton.disabled = false;
            downloadButton.disabled = false;
            previewContainer.classList.remove('hidden');
            clearAllIntervals();
        }, 60000);
    });
    
    // Function to update progress bar and text
    function updateProgress(percent, message) {
        if (progressBar && progressPercent) {
            progressBar.style.width = `${percent}%`;
            progressPercent.textContent = `${percent}%`;
            
            if (message && loadingText) {
                loadingText.textContent = message;
            }
            
            // Add transition class for smooth animation
            if (!progressBar.classList.contains('transitioning')) {
                progressBar.classList.add('transitioning');
            }
        }
    }
    
    // Function to start tracking progress
    function startProgressTracking() {
        // Clear any existing interval
        clearAllIntervals();
        
        // Start with simulation for initial progress until server responds
        let currentProgress = 5;
        let lastServerProgress = 0;
        let failedAttempts = 0;
        const maxFailedAttempts = 5;
        
        // First update with initial value
        updateProgress(currentProgress, 'Đang chuẩn bị tải xuống...');
        
        // Set up polling interval to check server for real progress
        progressInterval = setInterval(() => {
            // If we still don't have a download ID, use simulation
            if (!downloadId) {
                simulateProgress();
                return;
            }
            
            // Get the CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Check progress from server
            fetch('/check_progress/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({
                    'download_id': downloadId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Reset failed attempts counter on success
                failedAttempts = 0;
                
                // If we get valid progress data from server
                if (data && typeof data.progress !== 'undefined') {
                    // Only update if server progress is greater than current progress
                    // or if this is our first update from server
                    if (data.progress > lastServerProgress || lastServerProgress === 0) {
                        lastServerProgress = data.progress;
                        updateProgress(data.progress, data.message || 'Đang tải xuống...');
                        
                        // If download is complete, clear interval
                        if (data.status === 'complete' || data.status === 'error' || data.progress >= 100) {
                            console.log('Download complete or error:', data.status);
                            
                            // Force hide loading immediately for complete status
                            if (data.status === 'complete') {
                                loadingElement.classList.add('hidden');
                                previewContainer.classList.remove('hidden');
                                previewButton.disabled = false;
                                downloadButton.disabled = false;
                                clearAllIntervals();
                            } else {
                                // For other statuses, use a timeout
                                setTimeout(() => {
                                    console.log('Hiding loading after timeout');
                                    // Properly hide the loading element
                                    loadingElement.classList.add('hidden');
                                    
                                    // Re-enable buttons
                                    previewButton.disabled = false;
                                    downloadButton.disabled = false;
                                    previewContainer.classList.remove('hidden');
                                    
                                    if (data.status === 'error') {
                                        // If there was an error, show error message
                                        urlError.textContent = data.message || 'Có lỗi xảy ra trong quá trình tải xuống.';
                                    }
                                    clearAllIntervals();
                                }, 1000); // Show progress for a second before clearing
                            }
                        }
                    }
                } else {
                    // If no valid data, fall back to simulation
                    simulateProgress();
                }
            })
            .catch(error => {
                // Count failed attempts
                failedAttempts++;
                
                // If too many failed attempts, fall back to simulation
                if (failedAttempts > maxFailedAttempts) {
                    simulateProgress();
                }
            });
        }, 1000);  // Poll every second
        
        // Listen for page unload to stop the interval
        window.addEventListener('beforeunload', clearAllIntervals);
        
        // Simulation function for when server doesn't respond
        function simulateProgress() {
            // Simple simulation that increases progress gradually
            if (currentProgress < 95) {
                // Calculate increment based on current progress (slower as we progress)
                let increment = 0;
                
                if (currentProgress < 30) {
                    increment = Math.random() * 3 + 1; // Faster at start
                    updateProgress(Math.floor(currentProgress), 'Đang chuẩn bị tải xuống...');
                } else if (currentProgress < 70) {
                    increment = Math.random() * 2 + 0.5; // Medium speed
                    updateProgress(Math.floor(currentProgress), 'Đang tải xuống video...');
                } else {
                    increment = Math.random() * 1 + 0.2; // Slower near end
                    updateProgress(Math.floor(currentProgress), 'Đang xử lý file...');
                }
                
                currentProgress += increment;
            }
        }
    }
    
    // Function to clear all intervals
    function clearAllIntervals() {
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }
});
