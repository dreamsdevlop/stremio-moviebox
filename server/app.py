from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from config import settings
from logger import logger
from server.routes import router as main_router

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="MovieBox Stremio Addon", version=settings.VERSION)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MovieBox Stremio Addon</title>
        <link rel="icon" type="image/png" href="/assets/logo.png">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Outfit:wght@600;700&display=swap');
            body {
                font-family: 'Inter', sans-serif;
                background-color: #f4f4f5;
                color: #27272a;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                -webkit-font-smoothing: antialiased;
            }
            .paper {
                background: white;
                padding: 3.5rem 3rem;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 24px 48px -12px rgba(0, 0, 0, 0.08);
                max-width: 440px;
                width: 100%;
                box-sizing: border-box;
                text-align: center;
            }
            h1 { 
                font-family: 'Outfit', sans-serif;
                font-weight: 700; 
                margin: 0 0 0.5rem 0; 
                font-size: 32px;
                color: #09090b;
                letter-spacing: -0.5px;
            }
            p { 
                font-weight: 400; 
                color: #71717a; 
                line-height: 1.6; 
                font-size: 15px; 
                margin-bottom: 2.5rem; 
            }
            .btn {
                display: inline-block;
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
                color: white;
                text-align: center;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                transition: transform 0.1s, opacity 0.2s;
                box-sizing: border-box;
            }
            .btn:hover { 
                opacity: 0.9;
            }
            .btn-secondary {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                padding: 14px;
                background: #f4f4f5;
                color: #27272a;
                text-align: center;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                font-size: 15px;
                border: 1px solid #e4e4e7;
                transition: background 0.2s, transform 0.1s;
                box-sizing: border-box;
                cursor: pointer;
            }
            .btn-secondary:hover {
                background: #e4e4e7;
            }
            .btn-secondary:active { transform: scale(0.98); }
            
            .button-group {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-bottom: 2rem;
            }
            
            .tips {  
                margin-top: 2rem; 
                font-size: 14px; 
                color: #71717a; 
                line-height: 1.5;
                border-top: 1px solid #e4e4e7; 
                padding-top: 1.5rem; 
                text-align: left;
                display: flex;
                align-items: flex-start;
                gap: 8px;
            }

            .tips strong {
                color: #27272a;
                font-weight: 500;
            }
            .logo {
                width: 72px;
                height: 72px;
                border-radius: 18px;
                margin-bottom: 1.25rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }
        </style>
    </head>
    <body>
        <div class="paper">
            <img src="/logo.png" alt="MovieBox Logo" class="logo">
            <h1>MovieBox</h1>
            <p>Your self hosted Stremio addon is running successfully. Click below to add it to Stremio.</p>
            
            <div class="button-group">
                <a href="#" id="install-btn" class="btn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; margin-top: -2px;">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Install to Stremio
                </a>
                
                <button id="copy-btn" class="btn-secondary">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; margin-top: -1px;">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    Copy Manifest URL
                </button>
            </div>
            
            <div class="tips">
                <div>
                    <strong>Tip:</strong> If the 1 click install fails, use the Copy button above and paste the URL directly into your Stremio search bar!
                </div>
            </div>
        </div>

        <script>
            // We just use the root manifest directly without configuration prefixes.
            const host = window.location.host;
            
            // Stremio protocol for the 1-click button
            const installUrl = 'stremio://' + host + '/manifest.json';
            document.getElementById('install-btn').href = installUrl;
            
            // Raw HTTP protocol for manual copy-pasting (bypasses Stremio port-stripping bugs)
            const rawUrl = window.location.protocol + '//' + host + '/manifest.json';
            
            // Handle Copy Button
            const copyBtn = document.getElementById('copy-btn');
            copyBtn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(rawUrl);
                    const originalHtml = copyBtn.innerHTML;
                    copyBtn.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px; margin-top: -1px;">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        <span style="color: #16a34a">Copied!</span>
                    `;
                    setTimeout(() => {
                        copyBtn.innerHTML = originalHtml;
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy!', err);
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/logo.png")
async def get_logo():
    return FileResponse("assets/logo.png", media_type="image/png")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting MovieBox Addon on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "server.app:app", host=settings.HOST, port=settings.PORT, reload=True
    )
