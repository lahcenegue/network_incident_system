// Network Incident Management System - Base JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Network Incident Management System - Base JS Loaded');
    
    // Initialize all components
    initializeSidebar();
    initializeTooltips();
    initializeAlerts();
    initializeUserDropdown();
    updateTimestamps();
    
    // Auto-refresh active incidents count every 30 seconds
    setInterval(updateActiveIncidentsCount, 30000);
});

// Sidebar Navigation Management
function initializeSidebar() {
    const sidebarNav = document.querySelector('.sidebar-nav');
    const mobileToggle = document.querySelector('.mobile-sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarNav) {
        // Handle submenu toggles
        const submenuToggles = sidebarNav.querySelectorAll('.has-submenu > a');
        submenuToggles.forEach(toggle => {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                const parentLi = this.parentElement;
                const submenu = parentLi.querySelector('.submenu');
                
                // Close other submenus
                sidebarNav.querySelectorAll('.has-submenu.open').forEach(item => {
                    if (item !== parentLi) {
                        item.classList.remove('open');
                    }
                });
                
                // Toggle current submenu
                parentLi.classList.toggle('open');
            });
        });
        
        // Set active menu item based on current URL
        setActiveMenuItem();
    }
    
    // Mobile sidebar toggle
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('mobile-open');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && 
                !sidebar.contains(e.target) && 
                !mobileToggle.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }
}

// Set active menu item based on current URL
function setActiveMenuItem() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.sidebar-nav a');
    
    menuLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath && currentPath.startsWith(linkPath) && linkPath !== '/') {
            link.classList.add('active');
            // Open parent submenu if this is a submenu item
            const parentSubmenu = link.closest('.has-submenu');
            if (parentSubmenu) {
                parentSubmenu.classList.add('open');
            }
        } else if (linkPath === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

// Initialize Bootstrap tooltips (if Bootstrap is loaded)
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => 
            new bootstrap.Tooltip(tooltipTriggerEl)
        );
    }
}

// Auto-dismiss alerts after 5 seconds
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert && alert.parentNode) {
                        alert.remove();
                    }
                }, 300);
            }
        }, 5000);
    });
}

// User dropdown functionality
function initializeUserDropdown() {
    const userDropdown = document.querySelector('.user-dropdown');
    if (userDropdown) {
        const dropdownToggle = userDropdown.querySelector('.dropdown-toggle');
        const dropdownMenu = userDropdown.querySelector('.dropdown-menu');
        
        if (dropdownToggle && dropdownMenu) {
            dropdownToggle.addEventListener('click', function(e) {
                e.preventDefault();
                dropdownMenu.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(e) {
                if (!userDropdown.contains(e.target)) {
                    dropdownMenu.classList.remove('show');
                }
            });
        }
    }
}

// Update relative timestamps (e.g., "2 minutes ago")
function updateTimestamps() {
    const timestamps = document.querySelectorAll('[data-timestamp]');
    timestamps.forEach(element => {
        const timestamp = parseInt(element.dataset.timestamp);
        const now = Date.now();
        const diff = now - (timestamp * 1000);
        
        element.textContent = formatTimeAgo(diff);
    });
}

// Format time difference as "X minutes ago"
function formatTimeAgo(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

// Update active incidents count (placeholder - will be implemented with AJAX later)
function updateActiveIncidentsCount() {
    const countElements = document.querySelectorAll('.active-incidents-count');
    // This will be implemented when we add AJAX endpoints
    console.log('Active incidents count update scheduled');
}

// Utility functions for forms and validation
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of content body
    const contentBody = document.querySelector('.content-body');
    if (contentBody) {
        contentBody.insertBefore(notification, contentBody.firstChild);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Form validation helpers
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Incident severity color helper
function getIncidentSeverityClass(createdTime) {
    const now = new Date();
    const incident = new Date(createdTime);
    const diffHours = (now - incident) / (1000 * 60 * 60);
    
    if (diffHours < 1) return 'severity-white';
    if (diffHours < 2) return 'severity-yellow';
    if (diffHours < 4) return 'severity-orange';
    return 'severity-red';
}

// Export functions for use in other scripts
window.NetworkIncidentSystem = {
    showNotification,
    validateForm,
    getIncidentSeverityClass,
    formatTimeAgo
};