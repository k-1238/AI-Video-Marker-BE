# Video Editor

Video Editor is a full-stack application that allows users to input keywords and generate full-length videos composed of images, audio, and scene descriptions. The project utilizes a combination of Next.js for the frontend and backend API and Python for video processing.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- User-friendly interface for entering keywords and parameters.
- Backend processes user input to generate video scenes with images and audio.
- Full-length videos are rendered based on user-provided descriptions.
- Real-time progress updates during video generation.
- Downloadable videos upon completion.

---

## Technologies Used

### Frontend

- [Next.js](https://nextjs.org) (React Framework)
- [Material-UI](https://mui.com) (UI Components)

### Backend

- [Next.js API Routes](https://nextjs.org/docs/api-routes/introduction)
- [Python](https://www.python.org) (Video processing and rendering)

### Database

- [MongoDB](https://www.mongodb.com) (For user data and video-related metadata)

### Video Processing

- Python libraries such as OpenCV, MoviePy, or FFMPEG for video creation.

---

## Project Structure

├── pages/
│ ├── api/ # API routes
│ ├── app/ # Main video processing routes
│ └── index.tsx # Index pages
├── src/
│ ├── components/ # React components
│ ├── lib/ # Utility functions
│ └── pages/ # App pages
├── public/ # Static assets
└── utils/ # utility functions

---

## Setup and Installation

### Prerequisites

- [Node.js](https://nodejs.org) (v16+) - Recommended: v21
- [Python 3.9+](https://www.python.org) - Recommended v3.13
- [MongoDB](https://www.mongodb.com) - Recommended v7
- Package managers: `npm`
- [FFmpeg](https://ffmpeg.org) installed on your system.

### Steps

1. **Clone the repository**:

Copy and repositories and all it associated files to your destination folder

2. **Installation**

For full stack Next.js repository
```bash
npm install # Install dependencies for Next.js
```

For back end Python repository
```bash
pip install -r requirements.txt # Install dependencies for Python
```

3. **Setting up environment**

For back end Python repository
```bash
python -m venv venv
source venv/bin/activate # On macOS/Linux
venv\Scripts\activate # On Windows
```

For database MongoDB
- MongoDB Atlas Setup
- Create a MongoDB Atlas Account at MongoDB Atlas.
- Create a new Cluster and navigate to the Database Deployments section.
- Click "Connect", select "Connect Your Application", and copy the MongoDB connection string.
- Replace <username>, <password>, and <dbname> with your actual credentials.
- Update the .env file in the Next.js and Python repositories with the following example:
```env
MONGO_URL=mongodb+srv://<username>:<password>@cluster0.mongodb.net/<dbname>?retryWrites=true&w=majority
```

4. **Setting up environment variable**

For full stack Next.js repository
```
JWT_SECRET=REPLACE_KEY_HERE
NEXTAUTH_SECRET=REPLACE_KEY_HERE
DATABASE_URL=REPLACE_KEY_HERE_EXAMPLE_mongodb://127.0.0.1:27017/video-ai
MONGODB_URI=REPLACE_KEY_HERE_EXAMPLE_mongodb://127.0.0.1:27017/video-ai
VIDEO_BACKEND_URL=REPLACE_URL_HERE
GOOGLE_CLIENT_ID=REPLACE_KEY_HERE
GOOGLE_CLIENT_SECRET=REPLACE_KEY_HERE
```

For back end Python repository
```
OPENAI_API_KEY=REPLACE_KEY_HERE
OPENAI_MODEL=gpt-4o
OPENAI_TTS_MODEL=tts-1
PIXABAY_API_KEY=REPLACE_KEY_HERE
```

5. **Running**

For full stack Next.js repository
```bash
npm run dev # (for Next.js repository)
```

For back end Python repository
```bash
uvicorn main:app --reload # (for Python repository)
```
