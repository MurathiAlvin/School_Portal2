
document.addEventListener("DOMContentLoaded", function () {
    const passwordButtons = document.querySelectorAll(".toggle-password");

    passwordButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const targetId = button.dataset.target;
            const passwordInput = document.getElementById(targetId);

            if (!passwordInput) {
                return;
            }

            const isHidden = passwordInput.type === "password";

            passwordInput.type = isHidden ? "text" : "password";
            button.textContent = isHidden ? "Hide" : "Show";
            button.setAttribute(
                "aria-label",
                isHidden ? "Hide password" : "Show password"
            );
        });
    });
    // Password confirmation
    
const registerForm = document.getElementById("registerForm");

if (registerForm) {
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm_password");
    const message = document.getElementById("passwordMessage");

    function checkPasswords() {
        if (!confirmPassword.value) {
            message.textContent = "";
            confirmPassword.setCustomValidity("");
            return;
        }

        if (password.value !== confirmPassword.value) {
            message.textContent = "Passwords do not match.";
            confirmPassword.setCustomValidity("Passwords do not match.");
        } else {
            message.textContent = "Passwords match.";
            confirmPassword.setCustomValidity("");
        }
    }

    password.addEventListener("input", checkPasswords);
    confirmPassword.addEventListener("input", checkPasswords);
}

});
