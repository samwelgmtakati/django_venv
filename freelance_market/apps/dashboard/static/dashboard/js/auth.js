/**
 * Authentication Module
 * Handles user authentication with hardcoded users
 */

// Hardcoded users for demonstration
const users = [
	{
		id: 1,
		username: "client@example.com",
		password: "client123",
		firstName: "John",
		lastName: "Client",
		role: "client",
		isActive: true,
	},
	{
		id: 2,
		username: "freelancer@example.com",
		password: "freelancer123",
		firstName: "Jane",
		lastName: "Freelancer",
		role: "freelancer",
		isActive: true,
	},
];

// Check if user is logged in
function isAuthenticated() {
	return localStorage.getItem("currentUser") !== null;
}

// Get current user
function getCurrentUser() {
	const user = localStorage.getItem("currentUser");
	return user ? JSON.parse(user) : null;
}

// Login function
function login(username, password) {
	const user = users.find((u) => u.username === username && u.password === password);

	if (user && user.isActive) {
		// Store user data in localStorage (without password)
		const { password: _, ...userWithoutPassword } = user;
		localStorage.setItem("currentUser", JSON.stringify(userWithoutPassword));
		return { success: true, user: userWithoutPassword };
	}

	return { success: false, message: "Invalid username or password" };
}

// Logout function
function logout() {
	localStorage.removeItem("currentUser");
	window.location.href = "/login/";
}

// Register function (for future use with actual backend)
function register(userData) {
	// In a real app, this would make an API call to register the user
	// For now, we'll just add to our hardcoded users
	const newUser = {
		id: users.length + 1,
		...userData,
		isActive: true,
	};

	users.push(newUser);

	// Return the user without the password
	const { password, ...userWithoutPassword } = newUser;
	return { success: true, user: userWithoutPassword };
}

// Check if current user has required role
function hasRole(role) {
	const user = getCurrentUser();
	return user && user.role === role;
}

// Redirect to dashboard based on user role
function redirectToDashboard() {
	const user = getCurrentUser();
	if (!user) return;

	if (user.role === "client") {
		window.location.href = "/client/dashboard/";
	} else if (user.role === "freelancer") {
		window.location.href = "/freelancer/dashboard/";
	}
}

// Export functions
window.Auth = {
	login,
	logout,
	register,
	isAuthenticated,
	getCurrentUser,
	hasRole,
	redirectToDashboard,
};

// Auto-redirect if user is already logged in
document.addEventListener("DOMContentLoaded", function () {
	const publicPages = ["/login/", "/register/"];
	const currentPath = window.location.pathname;

	if (isAuthenticated() && publicPages.includes(currentPath)) {
		redirectToDashboard();
	}
});
