// Login Page JavaScript - Enhanced Functionality

document.addEventListener('DOMContentLoaded', function() {
    // Set current year in copyright
    document.getElementById('currentYear').textContent = new Date().getFullYear();
    
    // Initialize login functionality
    initializeLogin();
});

function initializeLogin() {
    const form = document.querySelector('.login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const togglePassword = document.getElementById('togglePassword');
    const toggleIcon = document.getElementById('toggleIcon');
    const submitButton = form.querySelector('.btn-login');
    const btnText = submitButton.querySelector('.btn-text');
    const btnLoading = submitButton.querySelector('.btn-loading');
    
    // Password toggle functionality
    if (togglePassword && passwordInput && toggleIcon) {
        togglePassword.addEventListener('click', function() {
            const isPassword = passwordInput.type === 'password';
            
            // Toggle input type
            passwordInput.type = isPassword ? 'text' : 'password';
            
            // Toggle icon
            toggleIcon.className = isPassword ? 'bx bx-show' : 'bx bx-hide';
            
            // Add visual feedback
            togglePassword.style.transform = 'scale(0.9)';
            setTimeout(() => {
                togglePassword.style.transform = 'scale(1)';
            }, 150);
            
            // Refocus input
            passwordInput.focus();
        });
    }
    
    // Form validation and submission
    if (form) {
        form.addEventListener('submit', function(e) {
            // Basic client-side validation
            if (!validateForm()) {
                e.preventDefault();
                return;
            }
            
            // Show loading state
            showLoadingState();
        });
    }
    
    // Input enhancements
    enhanceInputs([usernameInput, passwordInput]);
    
    // Auto-dismiss alerts
    autoDismissAlerts();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Focus management
    setupFocusManagement();
}

function validateForm() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    let isValid = true;
    
    // Clear previous error states
    clearErrorStates();
    
    // Username validation
    if (!username) {
        showFieldError('username', 'يرجى إدخال اسم المستخدم');
        isValid = false;
    } else if (username.length < 3) {
        showFieldError('username', 'اسم المستخدم يجب أن يكون 3 أحرف على الأقل');
        isValid = false;
    }
    
    // Password validation
    if (!password) {
        showFieldError('password', 'يرجى إدخال كلمة المرور');
        isValid = false;
    } else if (password.length < 6) {
        showFieldError('password', 'كلمة المرور يجب أن تكون 6 أحرف على الأقل');
        isValid = false;
    }
    
    return isValid;
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const formGroup = field.closest('.form-group');
    
    // Add error class
    field.classList.add('is-invalid');
    
    // Remove existing error message
    const existingError = formGroup.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.innerHTML = `<i class="bx bx-error-circle me-1"></i>${message}`;
    formGroup.appendChild(errorDiv);
    
    // Add shake animation
    field.style.animation = 'shake 0.5s ease-in-out';
    setTimeout(() => {
        field.style.animation = '';
    }, 500);
}

function clearErrorStates() {
    const invalidFields = document.querySelectorAll('.is-invalid');
    const errorMessages = document.querySelectorAll('.invalid-feedback');
    
    invalidFields.forEach(field => field.classList.remove('is-invalid'));
    errorMessages.forEach(error => error.remove());
}

function showLoadingState() {
    const submitButton = document.querySelector('.btn-login');
    const btnText = submitButton.querySelector('.btn-text');
    const btnLoading = submitButton.querySelector('.btn-loading');
    
    // Disable button
    submitButton.disabled = true;
    
    // Show loading state
    btnText.style.display = 'none';
    btnLoading.style.display = 'flex';
    
    // Add loading class for additional styling
    submitButton.classList.add('loading');
}

function hideLoadingState() {
    const submitButton = document.querySelector('.btn-login');
    const btnText = submitButton.querySelector('.btn-text');
    const btnLoading = submitButton.querySelector('.btn-loading');
    
    // Enable button
    submitButton.disabled = false;
    
    // Hide loading state
    btnText.style.display = 'block';
    btnLoading.style.display = 'none';
    
    // Remove loading class
    submitButton.classList.remove('loading');
}

function enhanceInputs(inputs) {
    inputs.forEach(input => {
        if (!input) return;
        
        // Add floating label effect
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Clear error state on input
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                this.classList.remove('is-invalid');
                const errorMessage = this.parentElement.querySelector('.invalid-feedback');
                if (errorMessage) {
                    errorMessage.remove();
                }
            }
        });
        
        // Add ripple effect on focus
        input.addEventListener('focus', function() {
            createRippleEffect(this);
        });
    });
}

function createRippleEffect(element) {
    const ripple = document.createElement('div');
    ripple.className = 'ripple-effect';
    element.style.position = 'relative';
    element.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
        if (ripple.parentNode) {
            ripple.parentNode.removeChild(ripple);
        }
    }, 600);
}

function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.animation = 'slideOutUp 0.5s ease-in-out forwards';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
        
        // Manual dismiss button
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                alert.style.animation = 'slideOutUp 0.5s ease-in-out forwards';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            });
        }
    });
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Enter to submit form (if focused on input)
        if (e.key === 'Enter') {
            const activeElement = document.activeElement;
            if (activeElement && (activeElement.id === 'username' || activeElement.id === 'password')) {
                e.preventDefault();
                document.querySelector('.btn-login').click();
            }
        }
        
        // Escape to clear form
        if (e.key === 'Escape') {
            clearForm();
        }
        
        // Ctrl/Cmd + K to focus username
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('username').focus();
        }
    });
}

function setupFocusManagement() {
    const inputs = document.querySelectorAll('input, button');
    
    // Create focus trap within login card
    const firstInput = inputs[0];
    const lastInput = inputs[inputs.length - 1];
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            // Forward tab
            if (!e.shiftKey && document.activeElement === lastInput) {
                e.preventDefault();
                firstInput.focus();
            }
            // Backward tab
            else if (e.shiftKey && document.activeElement === firstInput) {
                e.preventDefault();
                lastInput.focus();
            }
        }
    });
}

function clearForm() {
    const form = document.querySelector('.login-form');
    if (form) {
        form.reset();
        clearErrorStates();
        
        // Add clear animation
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.style.animation = 'fadeOut 0.3s ease-in-out';
            setTimeout(() => {
                input.value = '';
                input.style.animation = 'fadeIn 0.3s ease-in-out';
                setTimeout(() => {
                    input.style.animation = '';
                }, 300);
            }, 300);
        });
    }
}

// Utility function to show custom notifications
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="bx ${getNotificationIcon(type)} me-2"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">
            <i class="bx bx-x"></i>
        </button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto hide
    setTimeout(() => {
        hideNotification(notification);
    }, duration);
    
    // Manual close
    notification.querySelector('.notification-close').addEventListener('click', () => {
        hideNotification(notification);
    });
}

function hideNotification(notification) {
    notification.classList.remove('show');
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 300);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'bx-check-circle',
        error: 'bx-error-circle',
        warning: 'bx-error-circle',
        info: 'bx-info-circle'
    };
    return icons[type] || icons.info;
}

// Handle form submission errors (if any)
window.addEventListener('load', function() {
    // Hide loading state if page reloads due to error
    hideLoadingState();
    
    // Check for server-side errors and enhance them
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        // Focus on username field for retry
        setTimeout(() => {
            document.getElementById('username').focus();
        }, 500);
    }
});

// Add CSS for animations and additional styles
const additionalStyles = `
<style>
.is-invalid {
    border-color: var(--login-danger) !important;
    box-shadow: 0 0 0 0.125rem rgba(255, 59, 48, 0.25) !important;
}

.invalid-feedback {
    display: block;
    width: 100%;
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--login-danger);
    animation: slideInDown 0.3s ease-out;
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

@keyframes slideOutUp {
    from {
        opacity: 1;
        transform: translateY(0);
    }
    to {
        opacity: 0;
        transform: translateY(-20px);
    }
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.btn-login.loading {
    pointer-events: none;
}

.focused .form-label {
    color: var(--login-primary);
}

.ripple-effect {
    position: absolute;
    border-radius: 50%;
    background: rgba(0, 122, 255, 0.3);
    transform: scale(0);
    animation: ripple 0.6s linear;
    pointer-events: none;
}

@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.notification {
    position: fixed;
    top: 2rem;
    right: 2rem;
    background: white;
    border-radius: var(--login-border-radius);
    box-shadow: var(--login-shadow-lg);
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    transform: translateX(100%);
    transition: var(--login-transition);
    z-index: 9999;
    max-width: 400px;
    border-left: 4px solid var(--login-primary);
}

.notification.show {
    transform: translateX(0);
}

.notification-success {
    border-left-color: var(--login-success);
}

.notification-error {
    border-left-color: var(--login-danger);
}

.notification-warning {
    border-left-color: var(--login-warning);
}

.notification-content {
    display: flex;
    align-items: center;
    color: var(--login-gray-800);
    font-weight: 500;
}

.notification-close {
    background: none;
    border: none;
    color: var(--login-gray-500);
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 50%;
    transition: var(--login-transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
}

.notification-close:hover {
    background: var(--login-gray-100);
    color: var(--login-gray-700);
}

@media (max-width: 767.98px) {
    .notification {
        top: 1rem;
        right: 1rem;
        left: 1rem;
        max-width: none;
    }
}
</style>
`;

// Inject additional styles
document.head.insertAdjacentHTML('beforeend', additionalStyles);