/**
 * Freelance Market Dashboard - Main JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
	// Initialize tooltips
	var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
	var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
		return new bootstrap.Tooltip(tooltipTriggerEl);
	});

	// Toggle sidebar on mobile
	const sidebarToggle = document.getElementById("sidebarToggle");
	const sidebar = document.querySelector(".sidebar");
	const mainContent = document.querySelector(".main-content");
	let sidebarOverlay = null;

	if (sidebarToggle && sidebar) {
		sidebarToggle.addEventListener("click", function (e) {
			e.preventDefault();
			sidebar.classList.toggle("show");
			mainContent.classList.toggle("sidebar-open");

			// Add overlay when sidebar is open on mobile
			if (sidebar.classList.contains("show")) {
				sidebarOverlay = document.createElement("div");
				sidebarOverlay.className = "sidebar-overlay";
				sidebarOverlay.addEventListener("click", closeSidebar);
				document.body.appendChild(sidebarOverlay);
			} else {
				removeOverlay();
			}
		});
	}

	// Close sidebar when clicking on a nav link on mobile
	const navLinks = document.querySelectorAll(".sidebar .nav-link");
	navLinks.forEach(function (link) {
		link.addEventListener("click", function () {
			if (window.innerWidth < 992) {
				closeSidebar();
			}
		});
	});

	// Close sidebar when window is resized to desktop
	window.addEventListener("resize", function () {
		if (window.innerWidth >= 992) {
			closeSidebar();
		}
	});

	// Close sidebar function
	function closeSidebar() {
		if (sidebar) {
			sidebar.classList.remove("show");
			mainContent.classList.remove("sidebar-open");
			removeOverlay();
		}
	}

	// Remove overlay function
	function removeOverlay() {
		if (sidebarOverlay) {
			sidebarOverlay.remove();
			sidebarOverlay = null;
		} else {
			const existingOverlay = document.querySelector(".sidebar-overlay");
			if (existingOverlay) {
				existingOverlay.remove();
			}
		}
	}

	// Auto-hide alerts after 5 seconds
	const alerts = document.querySelectorAll(".alert");
	alerts.forEach(function (alert) {
		setTimeout(function () {
			const bsAlert = new bootstrap.Alert(alert);
			bsAlert.close();
		}, 5000);
	});

	// Add active class to current nav item
	const currentPath = window.location.pathname;
	const navItems = document.querySelectorAll(".sidebar .nav-link");

	navItems.forEach(function (item) {
		if (item.getAttribute("href") === currentPath) {
			item.classList.add("active");
		}
	});
});

// Export functions for use in other scripts if needed
window.FreelanceMarket = {
	closeSidebar: closeSidebar,
	showAlert: function (message, type = "success") {
		const alert = document.createElement("div");
		alert.className = `alert alert-${type} alert-dismissible fade show`;
		alert.role = "alert";
		alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

		const container = document.querySelector("main") || document.body;
		container.prepend(alert);

		// Auto-hide after 5 seconds
		setTimeout(() => {
			const bsAlert = new bootstrap.Alert(alert);
			bsAlert.close();
		}, 5000);
	},
};
