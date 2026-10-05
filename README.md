# 5G and AI-Powered Smart Road Safety System

This project is an end-to-end smart road safety system developed by the **OffByOne** team for the Teknofest 2026 5G and Artificial Intelligence Smart Road Safety Competition. The system aims to maximize traffic safety by integrating low-latency communication, real-time object detection, and a mobile user interface.

## 🏗 Architecture and Technologies

The project consists of three main components:

*   **Artificial Intelligence (Docker):** The system utilizes three separate YOLO models for real-time detection: Vehicle Type Model (YOLOv8n), License Plate Model (YOLOv8n), and Driver Behavior and Objects Model (YOLOv8m). The AI algorithm first detects vehicles with their types and license plates, then humans; it assumes the person in the front right is the driver and checks driver behaviors (seatbelt, phone usage, distracted driving, drinking water, yawning) only for them. The model records undetected seatbelt instances as violations. The dataset was prepared using Roboflow and Kaggle open-source data, along with unique data captured in a closed-traffic area; augmentations such as brightness, hue, blur, and noise were applied.
*   **Backend (FastAPI):** A high-performance asynchronous API server. It dynamically manages network quality and handles user authentication by integrating 5G Open Gateway (Quality on Demand & Number Verification) APIs. The server communicates via 3 service endpoints: one for the authentication, one for the AI module(uploading video for analysis and getting results), and one for the quality on demand.
*   **Mobile Application (Flutter):** A cross-platform (iOS/Android) mobile interface where users receive instant safety alerts, view road conditions, and interact with the system. The mobile side features direct API integrations through login and home screens.

## 📂 Project Structure

\`\`\`text
├── OffByOneAI/         # 3 separate YOLO model weights, data processing scripts, and Dockerfile
├── backend/            # FastAPI endpoints and 5G Open Gateway integrations
└── mobile_app/         # Flutter UI/UX components and API integrations
\`\`\`

## 🚀 Installation and Setup

Follow the steps below to deploy the project in your local environment or on a server.

### 1. Artificial Intelligence Module (Docker)
To start the image processing and model inference module:
\`\`\`bash
cd OffByOneAI
docker build -t teknofest/akilli-yol:latest .
docker run --rm -e PYTHONUNBUFFERED=1 -v $(pwd)/test_videosu.mp4:/app/data/input/video.mp4 -v $(pwd)/output:/app/data/output teknofest/akilli-yol:latest
\`\`\`

### 2. Backend (FastAPI)
To install the required Python dependencies and start the asynchronous server:
\`\`\`bash
cd backend
python3 -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 3. Mobile Application (Flutter)
To run the mobile application on a connected device or emulator:
\`\`\`bash
cd mobile_app
flutter pub get
flutter run
\`\`\`

## 🔌 API and Network Integrations

*   **Quality on Demand (QoD):** Optimizes network parameters to provide the low latency and high bandwidth required for image transmission during emergencies or high-density anomaly detections.
*   **Number Verification:** Ensures that application users are authenticated securely and passwordlessly directly through the telecom operator's mobile network.

## 👥 Team (OffByOne)

*   **Esranur Demirel:** Team Lead (Software Eng. 3rd Year)
*   **Emine Uğur:** Team Member (Software Eng. 3rd Year)

## 📊 Presentation
You can review our detailed project presentation here:
[OffByOne Project Presentation (PDF)](docs/OffByOne_Presentation.pdf)