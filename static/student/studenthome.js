const sidebar = document.querySelector(".sidebar");
const sidebarToggler = document.querySelector(".sidebar-toggler");
const menuToggler = document.querySelector(".menu-toggler");
const fullSidebarHeight = "calc(100vh - 32px)"

// toggle sidebar's collapsed state
sidebarToggler.addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
});

// adjust sidebar height and menu toggle text
const toggleMenu = (isMenuActive) => {
  sidebar.style.height = isMenuActive ? `${sidebar.scrollHeight}px` : collapsedSidebarHeight;
  menuToggler.querySelector("span").innerText = isMenuActive ? "close" : "menu";
}

// toggle menu-active and adjust height
menuToggler.addEventListener("click", () => {
  toggleMenu(sidebar.classList.toggle("menu-active"));
});

// adjust sidebar height on window resize
window.addEventListener("resize", () => {
  sidebar.classList.toggle("collapsed", window.innerWidth < 1024);
  toggleMenu(sidebar.classList.contains("menu-active"));
});


document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.save-button').forEach(button => {
    button.addEventListener('click', async (event) => {
      const button = event.currentTarget;
      const jobId = button.dataset.jobId;
      const isSaved = button.classList.contains('saved');
      const url = isSaved ? `/student/unsave/${jobId}` : `/student/save/${jobId}`;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        const result = await response.json();

        if (result.success) {
          button.classList.toggle('saved');
          const icon = button.querySelector('.material-symbols-rounded');
          if (button.classList.contains('saved')) {
            button.innerHTML = '<span class="material-symbols-rounded">star</span> Saved';
            if (window.location.pathname.includes('/student/saved')) {
              button.closest('.postings').remove();
            }
          } else {
            button.innerHTML = '<span class="material-symbols-rounded">star_outline</span> Save';
          }
        } else {
          console.error('Failed to update saved status:', result.error);
        }
      } catch (error) {
        console.error('Error:', error);
      }
    });
  });
});