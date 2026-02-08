// Login form handler
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const status = document.getElementById('status');

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        if (response.ok) {
            status.innerText = "Login successful! Redirecting...";
            setTimeout(() => {
                window.location.href = "/";
            }, 1000);
        } else {
            status.innerText = "Login failed: " + result.error;
        }
    } catch (e) {
        status.innerText = "Error: " + e.message;
    }
}

// Signin form handler
async function handleSignin(event) {
    event.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const status = document.getElementById('status');

    try {
        const response = await fetch('/signin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });

        const result = await response.json();

        if (response.ok) {
            status.innerText = "Registration successful! Redirecting...";
            setTimeout(() => {
                window.location.href = "/";
            }, 1000);
        } else {
            status.innerText = "Registration failed: " + result.error;
        }
    } catch (e) {
        status.innerText = "Error: " + e.message;
    }
}

// Add event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Login form
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Signin form
    const signinForm = document.querySelector('form[action="/signin"]');
    if (signinForm) {
        signinForm.addEventListener('submit', handleSignin);
    }
});
