document.addEventListener("DOMContentLoaded", function () {
	// Smooth scrolling for anchor links
	document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
		anchor.addEventListener("click", function (e) {
			e.preventDefault();
			const target = document.querySelector(this.getAttribute("href"));
			if (target) {
				window.scrollTo({
					top: target.offsetTop - 80,
					behavior: "smooth",
				});
			}
		});
	});

	// Add shadow to navbar on scroll
	const navbar = document.querySelector(".navbar");
	if (navbar) {
		window.addEventListener("scroll", function () {
			if (window.scrollY > 50) {
				navbar.classList.add("shadow");
				navbar.style.padding = "0.5rem 0";
			} else {
				navbar.classList.remove("shadow");
				navbar.style.padding = "1rem 0";
			}
		});
	}

	// Add active class to current nav item
	const currentLocation = location.href;
	const menuItems = document.querySelectorAll(".nav-link");
	const menuLength = menuItems.length;

	for (let i = 0; i < menuLength; i++) {
		if (menuItems[i].href === currentLocation) {
			menuItems[i].classList.add("active");
		}
	}
});
