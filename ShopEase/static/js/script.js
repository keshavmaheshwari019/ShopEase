document.addEventListener("DOMContentLoaded", () => {
    // Mobile menu toggle
    const hamburger = document.querySelector(".hamburger")
    const navLinks = document.querySelector(".nav-links")
  
    if (hamburger) {
      hamburger.addEventListener("click", () => {
        hamburger.classList.toggle("active")
        navLinks.classList.toggle("active")
      })
    }
  
    // Close flash messages
    const closeButtons = document.querySelectorAll(".close-btn")
  
    closeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        this.parentElement.style.display = "none"
      })
    })
  
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
      const flashMessages = document.querySelectorAll(".alert")
      flashMessages.forEach((message) => {
        message.style.display = "none"
      })
    }, 5000)
  
    // Dropdown menu for mobile
    const dropdownToggles = document.querySelectorAll(".dropdown-toggle")
  
    dropdownToggles.forEach((toggle) => {
      toggle.addEventListener("click", function (e) {
        if (window.innerWidth < 768) {
          e.preventDefault()
          const dropdownMenu = this.nextElementSibling
          dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block"
        }
      })
    })
  
    // Close dropdowns when clicking outside
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".dropdown")) {
        const dropdownMenus = document.querySelectorAll(".dropdown-menu")
        dropdownMenus.forEach((menu) => {
          menu.style.display = ""
        })
      }
    })
  
    // Quantity input validation
    const quantityInputs = document.querySelectorAll('input[type="number"]')
  
    quantityInputs.forEach((input) => {
      input.addEventListener("change", function () {
        const min = Number.parseInt(this.getAttribute("min"))
        const max = Number.parseInt(this.getAttribute("max"))
        const value = Number.parseInt(this.value)
  
        if (value < min) {
          this.value = min
        } else if (value > max) {
          this.value = max
        }
      })
    })
  })
  













