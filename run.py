#!/usr/bin/env python3
"""
Masai LMS Support System Startup Script (MongoDB Edition)

This script initializes the MongoDB database and starts the FastAPI server.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.app.db.init_db import init_database

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('lms_support.log')
        ]
    )

def main():
    """Main startup function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("Starting Masai LMS Support System (MongoDB Edition)...")
    
    try:
        # Initialize database
        print("Initializing MongoDB database...")
        init_database()
        print("MongoDB database initialized successfully!")
        
        # Start FastAPI server
        print("Starting API server...")
        print("Database Stack: MongoDB + Redis + Pinecone")
        print("Sample Credentials:")
        print("   Student: student1@masaischool.com / password123")
        print("   Admin: ec1@masaischool.com / admin123")
        print()
        print("API will be available at: http://localhost:8000")
        print("API Documentation: http://localhost:8000/docs")
        print("Knowledge Base Categories:")
        print("   - Program Details")
        print("   - Q&A") 
        print("   - Curriculum Documents")
        print()
        
        import uvicorn
        from backend.app.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            # reload=True
        )
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        print(f"Error starting system: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()