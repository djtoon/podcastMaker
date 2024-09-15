# AI Podcast Generator

This project is an AI-powered podcast generator that creates engaging audio content based on user-specified topics. It utilizes various AI models and services to generate a full podcast experience, including script creation, text-to-speech conversion, and video generation.

### personal note
This is a side project and prompts arent 100% but i had fun making it

## Features

- Generate podcast scripts with multiple speakers
- Create realistic text-to-speech audio for each speaker
- Generate cover images for the podcast
- Combine audio and images into a video format

## Prerequisites

- Python 3.7+
- FFmpeg installed and accessible
- AWS account with Bedrock access
- OpenAI API key
- Stability AI API key

## Installation

1. Clone this repository
2. Install required Python packages:
   ```pip install boto3 pydub requests```
3. Set up your environment variables or update the script with your API keys:
   - AWS credentials (aws_key_id, aws_secret, region)
   - OpenAI API key
   - Stability AI API key
4. Ensure FFmpeg is installed and the path is correctly set in the script

## Usage

To generate a podcast, use the `makePodcast` function:



## TODO

- Add support for Anthropic API for enhanced conversation generation
- Integrate OpenAI API for additional AI capabilities
- Explore and implement other AI APIs for creating more diverse and engaging conversation scripts
- Incorporate Eleven Labs for improved text-to-speech functionality
- Implement a user interface for easier interaction with the podcast generation process
- Add support for multiple languages and accents in the generated podcasts
- Implement error handling and logging for better debugging and maintenance
- Create a configuration file for easy management of API keys and settings
- Add unit tests and integration tests to ensure code reliability
- Optimize performance for faster podcast generation

