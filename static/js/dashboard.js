 
/**
 * Dashboard JavaScript for Indian Stock Trading System
 * Handles real-time updates, charts, and user interactions
 */

class TradingDashboard {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.charts = {};
        this.refreshTimer = null;
        this.websocket = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoRefresh();
        this.addAnimations();
        console.log('🚀 Trading Dashboard initialized');
    }

    setupEventListeners() {
        // Visibility change handler for performance
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
                this.refreshAll();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
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
        });

        // Window resize handler for responsive charts
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 250));

        // Error handling for unhandled promises
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.showNotification('System Error: ' + event.reason, 'error');
        });
    }

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.refreshAll();
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

            await Promise.allSettled(promises);
            this.updateLastRefreshTime();
            
        } catch (error) {
            console.error('Error during refresh:', error);
            this.showNotification('Failed to refresh data', 'warning');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async refreshPortfolio() {
        try {
            const response = await fetch('/api/portfolio');
            const data = await response.json();
            
            if (data && !data.error) {
                this.updatePortfolioDisplay(data);
                return data;
            } else {
                throw new Error(data.error || 'Failed to fetch portfolio data');
            }
        } catch (error) {
            console.error('Portfolio refresh error:', error);
            throw error;
        }
    }

    async refreshSignals() {
        try {
            const response = await fetch('/api/signals');
            const data = await response.json();
            
            if (data && !data.error) {
                this.updateSignalsDisplay(data);
                return data;
            } else {
                throw new Error(data.error || 'Failed to fetch signals');
            }
        } catch (error) {
            console.error('Signals refresh error:', error);
            throw error;
        }
    }

    async refreshSystemStatus() {
        try {
            const response = await fetch('/api/system_status');
            const data = await response.json();
            
            if (data && !data.error) {
                this.updateSystemStatusDisplay(data);
                return data;
            } else {
                throw new Error(data.error || 'Failed to fetch system status');
            }
        } catch (error) {
            console.error('System status refresh error:', error);
            throw error;
        }
    }

    async refreshMarketData() {
        try {
            const response = await fetch('/api/regime');
            const data = await response.json();
            
            if (data && !data.error) {
                this.updateMarketRegimeDisplay(data);
                return data;
            } else {
                throw new Error(data.error || 'Failed to fetch market data');
            }
        } catch (error) {
            console.error('Market data refresh error:', error);
            throw error;
        }
    }

    updatePortfolioDisplay(portfolio) {
        // Update total value
        const totalValueEl = document.querySelector('.stat-card:first-child h3');
        if (totalValueEl && portfolio.total_value !== undefined) {
            this.animateNumber(totalValueEl, portfolio.total_value, {
                prefix: '₹',
                decimals: 2,
                separator: ','
            });
        }

        // Update P&L
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
        this.updatePositionsTable(portfolio.positions);
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
        const tableBody = document.querySelector('table tbody');
        if (!tableBody || !Array.isArray(positions)) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        // Add new rows
        positions.forEach(position => {
            const row = this.createPositionRow(position);
            tableBody.appendChild(row);
        });
    }

    createPositionRow(position) {
        const row = document.createElement('tr');
        const pnlClass = position.unrealized_pnl >= 0 ? 'text-success' : 'text-danger';
        
        row.innerHTML = `
            <td class="fw-bold">${position.symbol}</td>
            <td>${position.quantity}</td>
            <td>₹${this.formatNumber(position.entry_price, 2)}</td>
            <td>₹${this.formatNumber(position.current_price, 2)}</td>
            <td class="${pnlClass}">₹${this.formatNumber(position.unrealized_pnl, 2)}</td>
            <td class="text-danger">₹${this.formatNumber(position.stop_loss, 2)}</td>
            <td class="text-success">₹${this.formatNumber(position.target_price, 2)}</td>
            <td>${position.entry_date}</td>
        `;
        
        row.classList.add('fade-in');
        return row;
    }

    animateNumber(element, targetValue, options = {}) {
        const { prefix = '', suffix = '', decimals = 0, separator = ',', duration = 1000 } = options;
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
    }

    animateProgressBar(progressBar, targetWidth) {
        const currentWidth = parseFloat(progressBar.style.width) || 0;
        const increment = (targetWidth - currentWidth) / 30;
        let width = currentWidth;

        const timer = setInterval(() => {
            width += increment;
            
            if ((increment > 0 && width >= targetWidth) || 
                (increment < 0 && width <= targetWidth)) {
                width = targetWidth;
                clearInterval(timer);
            }

            progressBar.style.width = `${Math.max(0, Math.min(100, width))}%`;
        }, 16);
    }

    formatNumber(value, decimals = 2, separator = ',') {
        return Number(value).toLocaleString('en-IN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    initializeCharts() {
        // Initialize portfolio chart if canvas exists
        const portfolioCanvas = document.getElementById('portfolioChart');
        if (portfolioCanvas) {
            this.charts.portfolio = this.createPortfolioChart(portfolioCanvas);
        }

        // Initialize P&L chart if canvas exists
        const pnlCanvas = document.getElementById('pnlChart');
        if (pnlCanvas) {
            this.charts.pnl = this.createPnLChart(pnlCanvas);
        }
    }

    createPortfolioChart(canvas) {
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

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;

        // Add styles for notification positioning
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
            animation: slideInRight 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    updateLastRefreshTime() {
        const timeElements = document.querySelectorAll('[data-last-update]');
        const now = new Date().toLocaleTimeString();
        
        timeElements.forEach(element => {
            element.textContent = now;
        });

        // Update last-update element if it exists
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = now;
        }
    }

    addAnimations() {
        // Add intersection observer for scroll animations
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

        // Observe all cards
        document.querySelectorAll('.card').forEach(card => {
            observer.observe(card);
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

    // API Helper Methods
    async updateSystem() {
        try {
            this.showNotification('Updating system...', 'info');
            const response = await fetch('/api/update_system', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showNotification('System updated successfully!', 'success');
                await this.refreshAll();
            } else {
                this.showNotification('Failed to update system: ' + data.message, 'danger');
            }
        } catch (error) {
            this.showNotification('Error updating system: ' + error.message, 'danger');
        }
    }

    async runTradingSession() {
        try {
            this.showNotification('Running trading session...', 'info');
            const response = await fetch('/api/run_trading_session', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showNotification('Trading session completed!', 'success');
                setTimeout(() => this.refreshAll(), 2000);
            } else {
                this.showNotification('Failed to run trading session: ' + data.message, 'danger');
            }
        } catch (error) {
            this.showNotification('Error running trading session: ' + error.message, 'danger');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TradingDashboard();
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
`;
document.head.appendChild(style);