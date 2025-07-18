// Global variables
let currentData = null;
let selectedPlayers = []; // Array of player selections with their frame data
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
    
    // Update total frames display
    document.getElementById('totalFrames').textContent = data.video_info.total_frames;
    
    // Update navigation button states
    updateNavigationButtons();
    
    // Display first frame (already processed)
    displayVideoFrame(data.video_info.first_frame);
}

function showFrame(frameIndex) {
    if (!currentData || currentData.type !== 'video') return;
    
    currentFrameIndex = parseInt(frameIndex);
    document.getElementById('currentFrame').textContent = currentFrameIndex + 1;
    document.getElementById('frameSlider').value = currentFrameIndex;
    
    // Update navigation button states
    updateNavigationButtons();
    
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
    
    // Highlight selected players on current frame
    ctx.strokeStyle = '#dc3545';
    ctx.lineWidth = 3;
    selectedPlayers.forEach(selection => {
        if (selection.frameNumber === currentFrameIndex && selection.playerIndex < players.length) {
            const [x1, y1, x2, y2] = players[selection.playerIndex].bbox;
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
    // Check if this player is already selected
    const existingSelectionIndex = selectedPlayers.findIndex(selection => 
        selection.playerIndex === playerIndex && selection.frameNumber === currentFrameIndex
    );
    
    if (existingSelectionIndex > -1) {
        // Remove existing selection
        selectedPlayers.splice(existingSelectionIndex, 1);
        console.log(`Removed player ${playerIndex + 1} from frame ${currentFrameIndex + 1}`);
    } else {
        // Add new selection with current frame data
        const newSelection = {
            playerIndex: playerIndex,
            frameNumber: currentFrameIndex,
            playerData: null,
            frameData: null
        };
        
        if (currentData.type === 'image') {
            newSelection.frameData = {
                players: currentData.players,
                balls: currentData.balls
            };
            newSelection.frameNumber = 0;
            newSelection.playerData = currentData.players[playerIndex];
        } else if (currentData.type === 'video') {
            newSelection.frameData = currentData.currentFrameData;
            newSelection.playerData = currentData.currentFrameData.players[playerIndex];
        }
        
        selectedPlayers.push(newSelection);
        console.log(`Selected player ${playerIndex + 1} on frame ${currentFrameIndex + 1}`);
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
        
        container.innerHTML = selectedPlayers.map((selection, index) => 
            `<span class="player-chip">
                Player ${selection.playerIndex + 1} (Frame ${selection.frameNumber + 1})
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

function removePlayerSelection(selectionIndex) {
    if (selectionIndex >= 0 && selectionIndex < selectedPlayers.length) {
        selectedPlayers.splice(selectionIndex, 1);
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
    } else if (data.type === 'video') {
        // Show detections from first frame
        const firstFrame = data.video_info.first_frame;
        document.getElementById('playerCount').textContent = firstFrame.players.length;
    }
}

function createHighlight() {
    if (!currentData || selectedPlayers.length === 0) {
        showAlert('Please select at least one player', 'warning');
        return;
    }
    
    console.log('Creating single highlight video with', selectedPlayers.length, 'freeze frames');
    
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    loadingModal.show();
    
    // Update loading modal text to show it's processing
    const modalBody = document.querySelector('#loadingModal .modal-body p');
    if (modalBody) {
        modalBody.textContent = 'Creating highlight video with multiple freeze frames...';
    }
    
    // Send all selections together for one video with multiple freeze frames
    fetch('/highlight', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            filename: currentData.filename,
            player_selections: selectedPlayers // Send all selections for multiple freeze frames
        })
    })
    .then(response => response.json())
    .then(data => {
        loadingModal.hide();
        
        if (data.error) {
            showAlert(data.error, 'danger');
            return;
        }
        
        // Create success message with download link
        let successMessage = `Highlight video created successfully with ${selectedPlayers.length} freeze frame(s)!`;
        if (data.output_file) {
            successMessage += `<br><a href="${data.download_url || `/download/${data.output_file}`}" class="btn btn-success mt-2" target="_blank">Download Highlight Video</a>`;
        }
        
        // Show persistent success alert (won't auto-hide)
        showAlert(successMessage, 'success', true);
    })
    .catch(error => {
        loadingModal.hide();
        console.error('Error:', error);
        showAlert('Error creating highlight: ' + error.message, 'danger');
    });
}

function showAlert(message, type, persistent = false) {
    const alertDiv = document.getElementById('uploadStatus');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = message; // Use innerHTML instead of textContent to allow HTML content
    alertDiv.style.display = 'block';
    
    // Only auto-hide non-persistent alerts (not success alerts with download links)
    if (!persistent) {
        setTimeout(() => {
            alertDiv.style.display = 'none';
        }, 5000);
    }
}

// Frame navigation functions
function nextFrame() {
    if (!currentData || currentData.type !== 'video') return;
    
    const maxFrame = currentData.totalFrames - 1;
    if (currentFrameIndex < maxFrame) {
        showFrame(currentFrameIndex + 1);
    }
}

function previousFrame() {
    if (!currentData || currentData.type !== 'video') return;
    
    if (currentFrameIndex > 0) {
        showFrame(currentFrameIndex - 1);
    }
}

function updateNavigationButtons() {
    if (!currentData || currentData.type !== 'video') return;
    
    const prevBtn = document.getElementById('prevFrameBtn');
    const nextBtn = document.getElementById('nextFrameBtn');
    
    if (prevBtn && nextBtn) {
        prevBtn.disabled = currentFrameIndex <= 0;
        nextBtn.disabled = currentFrameIndex >= currentData.totalFrames - 1;
    }
}

// Keyboard navigation
function handleKeyPress(event) {
    // Only handle arrow keys when video is displayed and not in input fields
    if (!currentData || currentData.type !== 'video' || 
        event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }
    
    switch(event.key) {
        case 'ArrowLeft':
            event.preventDefault();
            previousFrame();
            break;
        case 'ArrowRight':
            event.preventDefault();
            nextFrame();
            break;
    }
}

// Drag and drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.querySelector('.card-body');
    
    // Add keyboard event listener
    document.addEventListener('keydown', handleKeyPress);
    
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