/**
 * Enhanced Dashboard JavaScript with proper error handling and performance optimization
 */

class TradingDashboard {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.charts = {};
        this.refreshTimer = null;
        this.apiClient = new ApiClient();
        this.retryCount = 0;
        this.maxRetries = 3;
        this.isVisible = true;
        
        this.init();
    }

    init() {
        try {
            this.setupEventListeners();
            this.initializeCharts();
            this.startAutoRefresh();
            this.addAnimations();
            this.setupErrorHandling();
            console.log('🚀 Trading Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showAlert('Dashboard initialization failed. Please refresh the page.', 'danger');
        }
    }

    setupEventListeners() {
        // Visibility change handler for performance
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            if (this.isVisible) {
                this.startAutoRefresh();
                this.refreshAll();
            } else {
                this.stopAutoRefresh();
            }
        });

        // Keyboard shortcuts with proper error handling
        document.addEventListener('keydown', (e) => {
            try {
                if (e.ctrlKey || e.metaKey) {
                    switch(e.key) {
                        case 'r':
                            e.preventDefault();
                            this.refreshAll();
                            break;
                        case 'u':
                            e.preventDefault();
                            this.updateSystem();
                            break;
                        case 't':
                            e.preventDefault();
                            this.runTradingSession();
                            break;
                    }
                }
            } catch (error) {
                console.error('Keyboard shortcut error:', error);
            }
        });

        // Window resize handler with debouncing
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 250));

        // Network status handling
        window.addEventListener('online', () => {
            this.showAlert('Connection restored', 'success');
            this.refreshAll();
        });

        window.addEventListener('offline', () => {
            this.showAlert('Connection lost. Data may be outdated.', 'warning');
            this.stopAutoRefresh();
        });
    }

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.showAlert('An unexpected error occurred', 'danger');
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showAlert('System error detected', 'warning');
        });
    }

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            if (this.isVisible && navigator.onLine) {
                this.refreshAll();
            }
        }, this.refreshInterval);
        
        console.log('✅ Auto-refresh started');
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
        console.log('⏸️ Auto-refresh stopped');
    }

    async refreshAll() {
        try {
            this.showLoadingIndicator();
            
            const promises = [
                this.refreshPortfolio(),
                this.refreshSignals(),
                this.refreshSystemStatus(),
                this.refreshMarketData()
            ];

            const results = await Promise.allSettled(promises);
            
            // Check for failures
            const failures = results.filter(result => result.status === 'rejected');
            if (failures.length > 0) {
                console.warn(`${failures.length} refresh operations failed`);
                failures.forEach(failure => console.error(failure.reason));
            }

            this.updateLastRefreshTime();
            this.retryCount = 0; // Reset retry count on success
            
        } catch (error) {
            console.error('Error during refresh:', error);
            this.handleRefreshError(error);
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async refreshPortfolio() {
        try {
            const data = await this.apiClient.fetchWithRetry('/api/portfolio');
            if (data && !data.error) {
                this.updatePortfolioDisplay(data);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to fetch portfolio data');
            }
        } catch (error) {
            console.error('Portfolio refresh error:', error);
            throw error;
        }
    }

    async refreshSignals() {
        try {
            const data = await this.apiClient.fetchWithRetry('/api/signals');
            if (data && !data.error) {
                this.updateSignalsDisplay(data.signals || []);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to fetch signals');
            }
        } catch (error) {
            console.error('Signals refresh error:', error);
            throw error;
        }
    }

    async refreshSystemStatus() {
        try {
            const data = await this.apiClient.fetchWithRetry('/api/system_status');
            if (data && !data.error) {
                this.updateSystemStatusDisplay(data);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to fetch system status');
            }
        } catch (error) {
            console.error('System status refresh error:', error);
            throw error;
        }
    }

    async refreshMarketData() {
        try {
            const data = await this.apiClient.fetchWithRetry('/api/regime');
            if (data && !data.error) {
                this.updateMarketRegimeDisplay(data);
                return data;
            } else {
                throw new Error(data?.error || 'Failed to fetch market data');
            }
        } catch (error) {
            console.error('Market data refresh error:', error);
            throw error;
        }
    }

    handleRefreshError(error) {
        this.retryCount++;
        
        if (this.retryCount >= this.maxRetries) {
            this.showAlert(`System appears to be experiencing issues. Last error: ${error.message}`, 'danger');
            this.stopAutoRefresh();
            
            // Try to restart after 5 minutes
            setTimeout(() => {
                this.retryCount = 0;
                this.startAutoRefresh();
            }, 300000);
        } else {
            this.showAlert(`Refresh failed (attempt ${this.retryCount}). Retrying...`, 'warning');
        }
    }

    updatePortfolioDisplay(portfolio) {
        try {
            // Update total value with animation
            const totalValueEl = document.querySelector('.stat-card:first-child h3');
            if (totalValueEl && portfolio.total_value !== undefined) {
                this.animateNumber(totalValueEl, portfolio.total_value, {
                    prefix: '₹',
                    decimals: 2,
                    separator: ','
                });
            }

            // Update P&L with color coding
            const pnlEl = document.querySelector('.stat-card:first-child small');
            if (pnlEl && portfolio.total_pnl !== undefined) {
                const pnlText = `P&L: ₹${this.formatNumber(portfolio.total_pnl, 2)} (${this.formatNumber(portfolio.return_pct || 0, 2)}%)`;
                pnlEl.textContent = pnlText;
                
                // Update card color based on P&L
                const card = pnlEl.closest('.stat-card');
                if (card) {
                    card.classList.remove('success', 'danger');
                    card.classList.add(portfolio.total_pnl >= 0 ? 'success' : 'danger');
                }
            }

            // Update positions count
            const positionsEl = document.querySelector('.stat-card:nth-child(3) h3');
            if (positionsEl && portfolio.positions_count !== undefined) {
                this.animateNumber(positionsEl, portfolio.positions_count);
            }

            // Update positions table if exists
            if (portfolio.positions) {
                this.updatePositionsTable(portfolio.positions);
            }

        } catch (error) {
            console.error('Error updating portfolio display:', error);
        }
    }

    updateSignalsDisplay(signals) {
        const signalsContainer = document.querySelector('.signal-card')?.parentElement?.parentElement;
        if (!signalsContainer || !Array.isArray(signals)) return;

        // Add fade effect to existing signals
        const existingSignals = signalsContainer.querySelectorAll('.signal-card');
        existingSignals.forEach(card => card.classList.add('fade-out'));

        // Update signals count in header
        const signalsCountEl = document.querySelector('.card-header .badge');
        if (signalsCountEl) {
            signalsCountEl.textContent = `${signals.length} signals`;
        }

        // Show notification for new high-confidence signals
        const highConfidenceSignals = signals.filter(s => s.confidence >= 80);
        if (highConfidenceSignals.length > 0) {
            this.showNotification(`${highConfidenceSignals.length} high-confidence signals available!`, 'info');
        }
    }

    updateSystemStatusDisplay(status) {
        // Update status indicator
        const statusIndicator = document.getElementById('system-status');
        if (statusIndicator) {
            const iconClass = status.running ? 'text-success' : 'text-danger';
            statusIndicator.innerHTML = `<i class="fas fa-circle ${iconClass}"></i>`;
        }

        // Update navbar text
        const navbarText = document.querySelector('.navbar-text');
        if (navbarText) {
            const statusText = status.running ? 'System Online' : 'System Offline';
            navbarText.innerHTML = `
                <span id="system-status" class="status-indicator ${status.running ? 'online' : ''}">
                    <i class="fas fa-circle ${status.running ? 'text-success' : 'text-danger'}"></i>
                </span>
                ${statusText}
            `;
        }

        // Update error count if displayed
        if (status.errors > 0) {
            this.showNotification(`System has ${status.errors} errors`, 'warning');
        }
    }

    updateMarketRegimeDisplay(regime) {
        // Update regime indicator
        const regimeIndicators = document.querySelectorAll('.regime-indicator');
        regimeIndicators.forEach(indicator => {
            indicator.className = `regime-indicator regime-${regime.regime || 'sideways'}`;
        });

        // Update regime text
        const regimeTexts = document.querySelectorAll('.text-capitalize');
        regimeTexts.forEach(text => {
            if (text.textContent.toLowerCase().includes('unknown') || 
                ['bull', 'bear', 'sideways'].includes(text.textContent.toLowerCase())) {
                text.textContent = regime.regime || 'Unknown';
            }
        });

        // Update confidence badges
        const confidenceBadges = document.querySelectorAll('.badge-custom.bg-primary');
        confidenceBadges.forEach(badge => {
            if (badge.textContent.includes('%')) {
                badge.textContent = `${Math.round(regime.confidence || 0)}%`;
            }
        });

        // Update market factors if available
        if (regime.factors) {
            this.updateMarketFactors(regime.factors);
        }
    }

    updateMarketFactors(factors) {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        if (progressBars[0] && factors.stocks_above_ema21 !== undefined) {
            this.animateProgressBar(progressBars[0], factors.stocks_above_ema21);
        }
        
        if (progressBars[1] && factors.avg_rsi !== undefined) {
            this.animateProgressBar(progressBars[1], factors.avg_rsi);
        }
        
        if (progressBars[2] && factors.market_breadth !== undefined) {
            this.animateProgressBar(progressBars[2], factors.market_breadth * 100);
        }
        
        if (progressBars[3] && factors.price_momentum !== undefined) {
            this.animateProgressBar(progressBars[3], Math.max(0, factors.price_momentum + 50));
        }
    }

    updatePositionsTable(positions) {
        try {
            const tableBody = document.querySelector('table tbody');
            if (!tableBody || !Array.isArray(positions)) return;

            // Clear existing rows
            tableBody.innerHTML = '';

            // Add new rows with error handling
            positions.forEach((position, index) => {
                try {
                    const row = this.createPositionRow(position);
                    tableBody.appendChild(row);
                } catch (error) {
                    console.error(`Error creating row ${index}:`, error);
                }
            });

        } catch (error) {
            console.error('Error updating positions table:', error);
        }
    }

    createPositionRow(position) {
        const row = document.createElement('tr');
        const pnlClass = (position.unrealized_pnl || 0) >= 0 ? 'text-success' : 'text-danger';
        
        // Safe value extraction with defaults
        const symbol = position.symbol || 'N/A';
        const quantity = position.quantity || 0;
        const entryPrice = position.entry_price || 0;
        const currentPrice = position.current_price || 0;
        const unrealizedPnl = position.unrealized_pnl || 0;
        const stopLoss = position.stop_loss || 0;
        const targetPrice = position.target_price || 0;
        const entryDate = position.entry_date || 'N/A';
        
        row.innerHTML = `
            <td class="fw-bold">${this.escapeHtml(symbol)}</td>
            <td>${quantity}</td>
            <td>₹${this.formatNumber(entryPrice, 2)}</td>
            <td>₹${this.formatNumber(currentPrice, 2)}</td>
            <td class="${pnlClass}">₹${this.formatNumber(unrealizedPnl, 2)}</td>
            <td class="text-danger">₹${this.formatNumber(stopLoss, 2)}</td>
            <td class="text-success">₹${this.formatNumber(targetPrice, 2)}</td>
            <td>${this.escapeHtml(entryDate)}</td>
        `;
        
        row.classList.add('fade-in');
        return row;
    }

    // Utility functions for safety
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatNumber(value, decimals = 2, separator = ',') {
        try {
            const num = parseFloat(value) || 0;
            return num.toLocaleString('en-IN', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });
        } catch (error) {
            console.error('Number formatting error:', error);
            return '0.00';
        }
    }

    animateNumber(element, targetValue, options = {}) {
        const { prefix = '', suffix = '', decimals = 0, separator = ',', duration = 1000 } = options;
        
        try {
            const startValue = parseFloat(element.textContent.replace(/[^\d.-]/g, '')) || 0;
            const increment = (targetValue - startValue) / (duration / 16);
            let currentValue = startValue;

            const timer = setInterval(() => {
                currentValue += increment;
                
                if ((increment > 0 && currentValue >= targetValue) || 
                    (increment < 0 && currentValue <= targetValue)) {
                    currentValue = targetValue;
                    clearInterval(timer);
                }

                const formattedValue = this.formatNumber(currentValue, decimals, separator);
                element.textContent = `${prefix}${formattedValue}${suffix}`;
            }, 16);

        } catch (error) {
            console.error('Number animation error:', error);
            // Fallback to direct update
            element.textContent = `${options.prefix || ''}${this.formatNumber(targetValue, options.decimals || 0)}${options.suffix || ''}`;
        }
    }

    showAlert(message, type = 'info') {
        try {
            // Remove existing notifications of same type
            const existingAlerts = document.querySelectorAll(`.alert-${type}.notification`);
            existingAlerts.forEach(alert => alert.remove());

            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show notification`;
            alertDiv.innerHTML = `
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;

            alertDiv.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 400px;
                animation: slideInRight 0.3s ease-out;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            `;

            document.body.appendChild(alertDiv);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => alertDiv.remove(), 300);
                }
            }, 5000);

        } catch (error) {
            console.error('Error showing alert:', error);
        }
    }

    showLoadingIndicator() {
        const indicators = document.querySelectorAll('.loading-indicator');
        indicators.forEach(indicator => {
            indicator.style.display = 'inline-block';
        });
    }

    hideLoadingIndicator() {
        const indicators = document.querySelectorAll('.loading-indicator');
        indicators.forEach(indicator => {
            indicator.style.display = 'none';
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Initialize charts with error handling
    initializeCharts() {
        try {
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js not loaded, skipping charts');
                return;
            }

            const portfolioCanvas = document.getElementById('portfolioChart');
            if (portfolioCanvas) {
                this.charts.portfolio = this.createPortfolioChart(portfolioCanvas);
            }

            const pnlCanvas = document.getElementById('pnlChart');
            if (pnlCanvas) {
                this.charts.pnl = this.createPnLChart(pnlCanvas);
            }

        } catch (error) {
            console.error('Chart initialization error:', error);
        }
    }

    createPortfolioChart(canvas) {
        try {
            return new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: ['Cash', 'Positions'],
                    datasets: [{
                        data: [70, 30],
                        backgroundColor: ['#16a34a', '#2563eb'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Portfolio chart creation error:', error);
            return null;
        }
    }

    createPnLChart(canvas) {
        return new Chart(canvas, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        ticks: {
                            callback: (value) => '₹' + this.formatNumber(value, 0)
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }

    updateLastRefreshTime() {
        try {
            const timeElements = document.querySelectorAll('[data-last-update]');
            const now = new Date().toLocaleTimeString();
            
            timeElements.forEach(element => {
                element.textContent = now;
            });

            const lastUpdateEl = document.getElementById('last-update');
            if (lastUpdateEl) {
                lastUpdateEl.textContent = now;
            }
        } catch (error) {
            console.error('Error updating refresh time:', error);
        }
    }

    addAnimations() {
        try {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('fade-in');
                    }
                });
            }, observerOptions);

            document.querySelectorAll('.card').forEach(card => {
                observer.observe(card);
            });
        } catch (error) {
            console.error('Animation setup error:', error);
        }
    }

    // API helper methods
    async updateSystem() {
        try {
            this.showAlert('Updating system...', 'info');
            const data = await this.apiClient.fetchWithRetry('/api/update_system', { method: 'POST' });
            
            if (data.status === 'success') {
                this.showAlert('System updated successfully!', 'success');
                await this.refreshAll();
            } else {
                this.showAlert('Failed to update system: ' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('Error updating system: ' + error.message, 'danger');
        }
    }

    async runTradingSession() {
        try {
            this.showAlert('Running trading session...', 'info');
            const data = await this.apiClient.fetchWithRetry('/api/run_trading_session', { method: 'POST' });
            
            if (data.status === 'success') {
                this.showAlert('Trading session completed!', 'success');
                setTimeout(() => this.refreshAll(), 2000);
            } else {
                this.showAlert('Failed to run trading session: ' + data.message, 'danger');
            }
        } catch (error) {
            this.showAlert('Error running trading session: ' + error.message, 'danger');
        }
    }
}

// Enhanced API Client with retry logic and timeout handling
class ApiClient {
    constructor() {
        this.maxRetries = 3;
        this.retryDelay = 1000;
        this.timeout = 10000; // 10 seconds
    }

    async fetchWithRetry(url, options = {}) {
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);

                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                return data;

            } catch (error) {
                console.warn(`API call failed (attempt ${attempt}/${this.maxRetries}):`, error.message);

                if (attempt === this.maxRetries) {
                    throw new Error(`API call failed after ${this.maxRetries} attempts: ${error.message}`);
                }

                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
            }
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.dashboard = new TradingDashboard();
        console.log('✅ Dashboard loaded successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        document.body.innerHTML += `
            <div class="alert alert-danger position-fixed" style="top: 20px; right: 20px; z-index: 9999;">
                <strong>Dashboard Error:</strong> Failed to initialize. Please refresh the page.
            </div>
        `;
    }
});

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .fade-out {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .loading-indicator {
        display: none;
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #007bff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);