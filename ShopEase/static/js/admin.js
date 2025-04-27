document.addEventListener("DOMContentLoaded", () => {
  // Image upload functionality
  const uploadBtn = document.getElementById("upload-btn")
  const productImage = document.getElementById("product_image")
  const imageUrlInput = document.getElementById("image_url")
  const imagePreview = document.getElementById("image-preview")

  if (uploadBtn && productImage) {
    uploadBtn.addEventListener("click", () => {
      productImage.click()
    })

    productImage.addEventListener("change", function () {
      const file = this.files[0]
      if (file) {
        const formData = new FormData()
        formData.append("image", file)

        fetch("/admin/product/upload", {
          method: "POST",
          body: formData,
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              imageUrlInput.value = data.image_url
              imagePreview.innerHTML = `<img src="${data.image_url}" alt="Product Image">`
            } else {
              alert(data.error || "Error uploading image")
            }
          })
          .catch((error) => {
            console.error("Error:", error)
            alert("Error uploading image")
          })
      }
    })
  }

  // Image URL preview
  if (imageUrlInput) {
    imageUrlInput.addEventListener("input", function () {
      const url = this.value.trim()
      if (url) {
        imagePreview.innerHTML = `<img src="${url}" alt="Product Image">`
      } else {
        imagePreview.innerHTML = ""
      }
    })
  }

  // Sidebar toggle
  const sidebarToggle = document.getElementById("sidebar-toggle")
  const adminSidebar = document.getElementById("admin-sidebar")
  const adminMain = document.querySelector(".admin-main")

  if (sidebarToggle && adminSidebar) {
    sidebarToggle.addEventListener("click", () => {
      adminSidebar.classList.toggle("collapsed")
      if (adminMain) {
        adminMain.classList.toggle("expanded")
      }
    })
  }

  // User dropdown
  const userDropdown = document.querySelector(".admin-user-dropdown")

  if (userDropdown) {
    const dropdownToggle = userDropdown.querySelector("span")
    const dropdownMenu = userDropdown.querySelector(".dropdown-menu")

    if (dropdownToggle && dropdownMenu) {
      dropdownToggle.addEventListener("click", (e) => {
        e.stopPropagation()
        dropdownMenu.classList.toggle("show")
      })

      // Close dropdown when clicking outside
      document.addEventListener("click", () => {
        dropdownMenu.classList.remove("show")
      })
    }
  }

  // Carousel Navigation
  const carouselContainer = document.querySelector(".carousel-container")
  const prevBtn = document.querySelector(".carousel-prev")
  const nextBtn = document.querySelector(".carousel-next")

  if (carouselContainer && prevBtn && nextBtn) {
    const cardWidth = document.querySelector(".category-card")?.offsetWidth + 20 || 320 // card width + margin

    prevBtn.addEventListener("click", () => {
      carouselContainer.scrollBy({ left: -cardWidth, behavior: "smooth" })
    })

    nextBtn.addEventListener("click", () => {
      carouselContainer.scrollBy({ left: cardWidth, behavior: "smooth" })
    })
  }

  // Close flash messages
  const closeButtons = document.querySelectorAll(".close-btn")

  closeButtons.forEach((button) => {
    button.addEventListener("click", function () {
      this.parentElement.style.display = "none"
    })
  })
})
