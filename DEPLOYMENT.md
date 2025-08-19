# Deploying HighlightGenerator to Fly.io

This guide will walk you through deploying your Soccer Highlight Generator application to Fly.io.

## Prerequisites

1. **Fly.io Account**: Sign up at [fly.io](https://fly.io)
2. **Fly CLI**: Install the Fly CLI tool
3. **Docker**: Ensure Docker is installed and running

## Installation Steps

### 1. Install Fly CLI

**macOS (using Homebrew):**
```bash
brew install flyctl
```

**Linux/macOS (using curl):**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows:**
Download from [fly.io/docs/hands-on/install-flyctl/](https://fly.io/docs/hands-on/install-flyctl/)

### 2. Login to Fly.io

```bash
fly auth login
```

### 3. Create a Fly Volume (for persistent storage) - OPTIONAL

**Note**: Free tier doesn't support volumes, but the app will work with local storage.

If you upgrade to a paid plan later:
```bash
fly volumes create highlight_data --size 10 --region iad
```

### 4. Deploy the Application

From your project directory:

```bash
# Launch the app (first time)
fly launch

# Or if you want to use the existing fly.toml
fly deploy
```

### 5. Set Environment Variables (if needed)

```bash
fly secrets set ENVIRONMENT=production
```

## Configuration Details

### Fly.toml Configuration

The `fly.toml` file is configured with:

- **App Name**: `highlightgenerator`
- **Primary Region**: `iad` (Washington DC)
- **Memory**: 1GB RAM (optimized for free tier)
- **CPU**: 1 shared CPU
- **Port**: 8080
- **Health Check**: `/health` endpoint
- **Auto-scaling**: Enabled with min 0 machines
- **Storage**: Local temporary storage (no volumes needed)

### Docker Configuration

The `Dockerfile` includes:

- Python 3.11 slim base image
- OpenCV and computer vision dependencies
- YOLOv8 model pre-download
- Health check configuration
- Proper file permissions

## Application Features

### Web Interface
- Modern, responsive UI with drag-and-drop file upload
- Real-time processing status updates
- Support for video and image files
- Automatic download of processed results

### API Endpoints
- `GET /` - Main web interface
- `GET /health` - Health check endpoint
- `POST /upload` - File upload endpoint
- `GET /status/<task_id>` - Processing status
- `GET /download/<task_id>` - Download processed file
- `POST /api/detect` - Image detection API

### Supported File Types
- **Videos**: MP4, AVI, MOV, MKV (up to 30 seconds processing)
- **Images**: PNG, JPG, JPEG
- **Max File Size**: 50MB (free tier limit)

## Monitoring and Management

### View Application Status
```bash
fly status
```

### View Logs
```bash
fly logs
```

### Scale Application
```bash
# Scale to 2 instances
fly scale count 2

# Scale memory
fly scale memory 4096
```

### Restart Application
```bash
fly apps restart
```

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Docker build logs: `fly logs --build`
   - Ensure all dependencies are in requirements.txt

2. **Memory Issues**
   - Increase memory allocation in fly.toml
   - Monitor memory usage: `fly status`

3. **File Upload Issues**
   - Check file size limits
   - Verify supported file types

4. **Processing Timeouts**
   - Increase timeout settings
   - Consider scaling resources

### Debug Commands

```bash
# SSH into the running container
fly ssh console

# View detailed app info
fly info

# Check app configuration
fly config show
```

## Cost Optimization

### Free Tier Optimization
The app is optimized for Fly.io's free tier:
- **Memory**: 1GB RAM (within free tier limits)
- **CPU**: Shared CPU (cost-effective)
- **Storage**: Local temporary storage (no volume costs)
- **Auto-scaling**: Min 0 machines (saves resources when idle)
- **File Limits**: 50MB max file size, 30 seconds video processing

### Resource Management
- Efficient memory usage for video processing
- Automatic cleanup of temporary files
- Optimized for short video clips
- No persistent storage costs

## Security Considerations

1. **File Upload Security**
   - File type validation
   - File size limits
   - Secure filename handling

2. **Environment Variables**
   - Use Fly secrets for sensitive data
   - Never commit secrets to version control

3. **Network Security**
   - HTTPS enforced
   - Health checks enabled

## Performance Tips

1. **Video Processing**
   - Large videos may take time to process
   - Consider implementing video compression
   - Use progress indicators for user feedback

2. **Memory Management**
   - Process videos in chunks if needed
   - Clean up temporary files
   - Monitor memory usage

## Support

For issues with:
- **Fly.io**: Check [fly.io/docs](https://fly.io/docs)
- **Application**: Check logs with `fly logs`
- **Deployment**: Use `fly status` and `fly info`

## Next Steps

After deployment:
1. Test the application with sample videos
2. Monitor performance and costs
3. Set up monitoring and alerts
4. Consider implementing additional features like:
   - User authentication
   - Batch processing
   - Advanced video analytics 