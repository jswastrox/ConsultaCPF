(function () {
  "use strict";

  var toggle = document.getElementById("nav-toggle");
  var backdrop = document.getElementById("nav-backdrop");
  var closeBtn = document.getElementById("nav-drawer-close");
  var drawer = document.getElementById("main-nav-drawer");

  function setNavOpen(open) {
    if (!toggle || !backdrop) return;
    document.body.classList.toggle("nav-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    backdrop.hidden = !open;
    document.body.style.overflow = open ? "hidden" : "";
  }

  if (toggle && backdrop) {
    setNavOpen(false);
    toggle.addEventListener("click", function () {
      setNavOpen(!document.body.classList.contains("nav-open"));
    });
    backdrop.addEventListener("click", function () {
      setNavOpen(false);
    });
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        setNavOpen(false);
      });
    }
    if (drawer) {
      drawer.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
          setNavOpen(false);
        });
      });
    }
  }

  var menu = document.getElementById("header-user-menu");
  var trigger = document.getElementById("user-menu-trigger");
  var dropdown = document.getElementById("user-menu-dropdown");
  if (menu && trigger && dropdown) {
    trigger.addEventListener("click", function (event) {
      event.stopPropagation();
      var open = dropdown.hasAttribute("hidden");
      if (open) {
        dropdown.removeAttribute("hidden");
        menu.classList.add("open");
        trigger.setAttribute("aria-expanded", "true");
      } else {
        dropdown.setAttribute("hidden", "");
        menu.classList.remove("open");
        trigger.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("click", function () {
      dropdown.setAttribute("hidden", "");
      menu.classList.remove("open");
      trigger.setAttribute("aria-expanded", "false");
    });
  }
})();
