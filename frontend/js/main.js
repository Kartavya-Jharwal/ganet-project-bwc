/**
 * BWC Portfolio | Phase 33 Stateful Frontend Engineering
 * main.js - Core telemetry and hydration engine
 */

const LOCAL_DATA_SOURCE = '../docs/backtest-results.json';

class BwcTelemetry {
    constructor() {
        this.store = {};
        this.dom = {
            kpiArea: document.querySelector('.l-kpi-grid'),
            factorList: document.querySelector('.factor-list'),
            varMetric: document.querySelector('.kpi-value:nth-child(2)'),
            videoPlaceholder: document.querySelector('.viz-placeholder'),
            videoSelector: null,
            statusIndicator: document.querySelector('.status-indicator')
        };
        this.videos = [
            
        ];
    }

    async init() {
        console.log("[BWC] Booting Stateful Telemetry Engine...");
        this.dom.statusIndicator.classList.add('loading');
        
        // Phase 35: Live Appwrite WebSockets Initialization
        this.initAppwrite();

        await this.fetchData();
        this.hydrateDOM();
        this.mountVideoPlayer();

        this.dom.statusIndicator.classList.remove('loading');
        this.dom.statusIndicator.classList.add('live');
    }

    initAppwrite() {
        if (!window.Appwrite) {
            console.warn("[BWC] Appwrite SDK not found. Falling back to local data.");
            return;
        }

        console.log("[BWC] Connecting to Appwrite Telemetry Stream...");
        const { Client, Databases } = window.Appwrite;
        
        this.client = new Client()
            .setEndpoint('https://cloud.appwrite.io/v1') // Defaulting to cloud, ideally env var
            .setProject('bwc-quant-live'); // Mock Project ID

        this.databases = new Databases(this.client);

        // Phase 35: Real-time WebSocket connection to the signals collection
        try {
            this.client.subscribe('databases.bwc_db.collections.signals.documents', response => {
                console.log("[BWC] Live Telemetry Update Received:", response);
                
                // Flash the status indicator to show data reception
                this.dom.statusIndicator.style.background = 'var(--text-primary)';
                setTimeout(() => {
                    this.dom.statusIndicator.style.background = 'var(--positive-color)';
                }, 150);

                if (response.events.includes('databases.*.collections.*.documents.*.create')) {
                    this.handleNewLiveSignal(response.payload);
                }
            });
        } catch (err) {
            console.warn("[BWC] WebSocket Subscription Failed:", err);
        }
    }

    handleNewLiveSignal(signalData) {
        // Logic to dynamically inject new data into the DOM
        console.log("New Signal:", signalData.ticker, signalData.action);
        // Will morph UI dynamically once data structures match
    }

    async fetchData() {
        try {
            // For now, load local static mock data. In Phase 35, we'll swap to WebSocket/Appwrite
            const res = await fetch(LOCAL_DATA_SOURCE);
            if(res.ok) {
                this.store = await res.json();
            } else {
                this.mockStore();
            }
        } catch (err) {
            console.warn('[BWC] Data fetch failed, defaulting to memory store.', err);
            this.mockStore();
        }
    }

    mockStore() {
        this.store = {
            kpi: {
                mc_hurdle: "94.2%",
                var_5: "-2.14%",
                beta: "0.85"
            },
            factors: [
                { name: "MKT (Beta)", value: 0.85, width: 85 },
                { name: "SMB (Size)", value: 0.30, width: 30 },
                { name: "HML (Value)", value: 0.65, width: 65 },
                { name: "MOM (Momentum)", value: 0.22, width: 22 }
            ],
            videos: [
                { id: "Scene4_AlphaBetaOrthogonality", name: "Alpha/Beta Orthogonality", file: "Scene4_AlphaBetaOrthogonality.mp4" },
                { id: "StochasticMonteCarloInsight", name: "Stochastic GBM", file: "StochasticMonteCarloInsight.mp4" },
                { id: "FamaFrenchAttributionInsight", name: "Fama-French Attribution", file: "FamaFrenchAttributionInsight.mp4" }
            ]
        };
    }

    hydrateDOM() {
        // Hydrate factors dynamically
        if(this.store.factors && this.dom.factorList) {
            this.dom.factorList.innerHTML = this.store.factors.map(f => `
                <li class="factor-item">
                    <div class="factor-header">
                        <span class="factor-name">${f.name}</span>
                        <span class="factor-val">${f.value.toFixed(2)}</span>
                    </div>
                    <div class="factor-bar"><div class="fill" style="width: ${f.width}%"></div></div>
                </li>
            `).join('');
        }
        
        // Add minimal interactions (Phase 31 motion layering)
        document.querySelectorAll('.kpi-card').forEach(el => {
            el.addEventListener('mouseenter', () => {
                el.style.transform = 'translateY(-2px)';
            });
            el.addEventListener('mouseleave', () => {
                el.style.transform = 'translateY(0)';
            });
        });
    }

    mountVideoPlayer() {
        if (!this.store.videos || !this.store.videos.length) return;
        
        // Construct the video element and a native selector
        const videoHTML = `
            <div class="video-wrapper" style="position: relative; width: 100%; height: 100%; display: flex; flex-direction: column;">
                <video id="manim-player" autoplay loop muted playsinline style="width: 100%; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
                    <source src="./assets/videos/${this.store.videos[0].file}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <div class="video-controls" style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: flex-end;">
                    <select id="video-selector" class="nav-select text-body">
                        ${this.store.videos.map(v => `<option value="${v.file}">${v.name}</option>`).join('')}
                    </select>
                </div>
            </div>
        `;
        
        this.dom.videoPlaceholder.innerHTML = videoHTML;
        
        const player = document.getElementById('manim-player');
        const selector = document.getElementById('video-selector');
        
        selector.addEventListener('change', (e) => {
            player.src = `./assets/videos/${e.target.value}`;
            player.play();
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.bwcApp = new BwcTelemetry();
    window.bwcApp.init();
});