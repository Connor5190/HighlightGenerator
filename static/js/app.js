// Global variables
let currentData = null;
let selectedPlayers = [];
let currentFrameIndex = 0;

// File upload handling
function handleFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if (fileInput.files.length > 0) {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Analyze';
    } else {
        uploadBtn.disabled = true;
    }
}

function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a file first', 'warning');
        return;
    }
    
    console.log('Uploading file:', file.name, 'Size:', file.size, 'bytes');
    
    // Show loading modal
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    loadingModal.show();
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Upload response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Upload response data:', data);
        loadingModal.hide();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        currentData = data;
        selectedPlayers = [];
        
        if (data.type === 'image') {
            console.log('Processing image with', data.players.length, 'players');
            displayImage(data);
        } else if (data.type === 'video') {
            console.log('Processing video with', data.video_info.total_frames, 'frames');
            displayVideo(data);
        }
        
        updateDetectionResults(data);
        showAlert('File processed successfully!', 'success');
    })
    .catch(error => {
        loadingModal.hide();
        console.error('Upload error:', error);
        showAlert('Error processing file: ' + error.message, 'danger');
    });
}

function displayImage(data) {
    // Hide other containers
    document.getElementById('videoContainer').style.display = 'none';
    document.getElementById('placeholder').style.display = 'none';
    
    // Show image container
    const imageContainer = document.getElementById('imageContainer');
    imageContainer.style.display = 'block';
    
    const canvas = document.getElementById('imageCanvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Draw detection boxes
        drawDetections(ctx, data.players, data.balls);
    };
    img.src = 'data:image/jpeg;base64,' + data.image;
    
    // Add click event listener
    canvas.onclick = function(event) {
        handleCanvasClick(event, data.players, canvas);
    };
}

function displayVideo(data) {
    // Hide other containers
    document.getElementById('imageContainer').style.display = 'none';
    document.getElementById('placeholder').style.display = 'none';
    
    // Show video container
    const videoContainer = document.getElementById('videoContainer');
    videoContainer.style.display = 'block';
    
    // Setup frame slider with total frames
    const frameSlider = document.getElementById('frameSlider');
    frameSlider.max = data.video_info.total_frames - 1;
    frameSlider.value = 0;
    currentFrameIndex = 0;
    
    // Store video info globally
    currentData.totalFrames = data.video_info.total_frames;
    currentData.fps = data.video_info.fps;
    
    // Display first frame (already processed)
    displayVideoFrame(data.video_info.first_frame);
}

function showFrame(frameIndex) {
    if (!currentData || currentData.type !== 'video') return;
    
    currentFrameIndex = parseInt(frameIndex);
    document.getElementById('currentFrame').textContent = currentFrameIndex + 1;
    
    // Show loading indicator
    const canvas = document.getElementById('videoCanvas');
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#6c757d';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Loading frame...', canvas.width / 2, canvas.height / 2);
    
    // Fetch frame from server
    fetch(`/get_frame/${currentData.filename}/${currentFrameIndex}`)
        .then(response => response.json())
        .then(frameData => {
            if (frameData.error) {
                console.error('Error loading frame:', frameData.error);
                return;
            }
            displayVideoFrame(frameData);
        })
        .catch(error => {
            console.error('Error fetching frame:', error);
        });
}

function displayVideoFrame(frameData) {
    const canvas = document.getElementById('videoCanvas');
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Draw detection boxes
        drawDetections(ctx, frameData.players, frameData.balls);
    };
    img.src = 'data:image/jpeg;base64,' + frameData.image;
    
    // Add click event listener
    canvas.onclick = function(event) {
        handleCanvasClick(event, frameData.players, canvas);
    };
    
    // Store current frame data for player selection
    currentData.currentFrameData = frameData;
}

function drawDetections(ctx, players, balls) {
    // Draw players in blue
    ctx.strokeStyle = '#007bff';
    ctx.lineWidth = 2;
    
    players.forEach((player, index) => {
        const [x1, y1, x2, y2] = player.bbox;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        
        // Add label
        ctx.fillStyle = '#007bff';
        ctx.font = '14px Arial';
        ctx.fillText(`Player ${index + 1}`, x1, y1 - 5);
    });
    
    // Draw balls in green
    ctx.strokeStyle = '#28a745';
    balls.forEach(ball => {
        const [x1, y1, x2, y2] = ball.bbox;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        
        // Add label
        ctx.fillStyle = '#28a745';
        ctx.font = '14px Arial';
        ctx.fillText('Ball', x1, y1 - 5);
    });
    
    // Highlight selected players
    ctx.strokeStyle = '#dc3545';
    ctx.lineWidth = 3;
    selectedPlayers.forEach(playerIndex => {
        if (playerIndex < players.length) {
            const [x1, y1, x2, y2] = players[playerIndex].bbox;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        }
    });
}

function handleCanvasClick(event, players, canvas) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;
    
    // Find clicked player
    for (let i = 0; i < players.length; i++) {
        const [x1, y1, x2, y2] = players[i].bbox;
        
        if (x >= x1 && x <= x2 && y >= y1 && y <= y2) {
            togglePlayerSelection(i);
            break;
        }
    }
}

function togglePlayerSelection(playerIndex) {
    const index = selectedPlayers.indexOf(playerIndex);
    
    if (index > -1) {
        // Remove from selection
        selectedPlayers.splice(index, 1);
    } else {
        // Add to selection
        selectedPlayers.push(playerIndex);
    }
    
    updateSelectedPlayersDisplay();
    redrawCurrentFrame();
}

function updateSelectedPlayersDisplay() {
    const container = document.getElementById('selectedPlayersList');
    const card = document.getElementById('selectedPlayersCard');
    const createBtn = document.getElementById('createHighlightBtn');
    const clearBtn = document.getElementById('clearBtn');
    
    if (selectedPlayers.length > 0) {
        card.style.display = 'block';
        createBtn.style.display = 'inline-block';
        clearBtn.style.display = 'inline-block';
        
        container.innerHTML = selectedPlayers.map(index => 
            `<span class="player-chip">
                Player ${index + 1}
                <span class="remove-btn" onclick="removePlayerSelection(${index})">&times;</span>
            </span>`
        ).join('');
    } else {
        card.style.display = 'none';
        createBtn.style.display = 'none';
        clearBtn.style.display = 'none';
        container.innerHTML = '';
    }
}

function removePlayerSelection(playerIndex) {
    const index = selectedPlayers.indexOf(playerIndex);
    if (index > -1) {
        selectedPlayers.splice(index, 1);
        updateSelectedPlayersDisplay();
        redrawCurrentFrame();
    }
}

function clearSelections() {
    selectedPlayers = [];
    updateSelectedPlayersDisplay();
    redrawCurrentFrame();
}

function redrawCurrentFrame() {
    if (!currentData) return;
    
    if (currentData.type === 'image') {
        displayImage(currentData);
    } else if (currentData.type === 'video') {
        showFrame(currentFrameIndex);
    }
}

function updateDetectionResults(data) {
    const resultsCard = document.getElementById('detectionResults');
    resultsCard.style.display = 'block';
    
    if (data.type === 'image') {
        document.getElementById('playerCount').textContent = data.players.length;
        document.getElementById('ballCount').textContent = data.balls.length;
    } else if (data.type === 'video') {
        // Show detections from first frame
        const firstFrame = data.video_info.first_frame;
        document.getElementById('playerCount').textContent = firstFrame.players.length;
        document.getElementById('ballCount').textContent = firstFrame.balls.length;
    }
}

function createHighlight() {
    if (!currentData || selectedPlayers.length === 0) {
        showAlert('Please select at least one player', 'warning');
        return;
    }
    
    // Get current frame data to extract selected player information
    let currentFrameData = null;
    let selectedFrameNumber = 0;
    
    if (currentData.type === 'image') {
        currentFrameData = {
            players: currentData.players,
            balls: currentData.balls
        };
        selectedFrameNumber = 0; // Images don't have frame numbers
    } else if (currentData.type === 'video') {
        currentFrameData = currentData.currentFrameData || currentData.video_info.first_frame;
        selectedFrameNumber = currentFrameIndex; // Use the current frame index for freeze frame
    }
    
    if (!currentFrameData || !currentFrameData.players) {
        showAlert('No player data available. Please navigate through frames first.', 'warning');
        return;
    }
    
    // Extract selected player data
    const selectedFrameData = [];
    selectedPlayers.forEach(playerIndex => {
        if (playerIndex < currentFrameData.players.length) {
            selectedFrameData.push(currentFrameData.players[playerIndex]);
        }
    });
    
    if (selectedFrameData.length === 0) {
        showAlert('Selected players not found in current frame', 'warning');
        return;
    }
    
    console.log('Creating highlight with player data:', selectedFrameData);
    console.log('Selected frame number for freeze effect:', selectedFrameNumber);
    
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    loadingModal.show();
    
    // Update loading modal text to show it's processing
    const modalBody = document.querySelector('#loadingModal .modal-body p');
    if (modalBody) {
        modalBody.textContent = 'Creating highlight video with freeze frames and player tracking...';
    }
    
    fetch('/highlight', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: currentData.filename,
            selected_players: selectedPlayers,
            selected_frame_data: selectedFrameData,
            selected_frame_number: selectedFrameNumber
        })
    })
    .then(response => response.json())
    .then(data => {
        loadingModal.hide();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        showAlert(`Highlight created successfully! ${data.message}`, 'success');
        
        // Add download link
        if (data.output_file) {
            const downloadLink = document.createElement('a');
            downloadLink.href = data.download_url || `/download/${data.output_file}`;
            downloadLink.textContent = 'Download Highlight Video';
            downloadLink.className = 'btn btn-success mt-2';
            downloadLink.target = '_blank';
            
            const alertDiv = document.querySelector('.alert-success');
            if (alertDiv) {
                alertDiv.appendChild(document.createElement('br'));
                alertDiv.appendChild(downloadLink);
            }
        }
    })
    .catch(error => {
        loadingModal.hide();
        console.error('Error:', error);
        showAlert('Error creating highlight: ' + error.message, 'danger');
    });
}

function showAlert(message, type) {
    const alertDiv = document.getElementById('uploadStatus');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 5000);
}

// Drag and drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.querySelector('.card-body');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight(e) {
        uploadArea.classList.add('dragover');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('dragover');
    }
    
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload();
        }
    }
});