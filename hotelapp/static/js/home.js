const $prev = document.querySelector(".prev");
const $next = document.querySelector(".next");
const header = document.querySelector("header");
header.classList.add("home__header");

$next.addEventListener("click", () => {
  const items = document.querySelectorAll(".slideshow__item");
  document.querySelector(".slideshow__inner").appendChild(items[0]);
  console.log("click");
});

$prev.addEventListener("click", () => {
  const items = document.querySelectorAll(".slideshow__item");
  document.querySelector(".slideshow__inner").prepend(items[items.length - 1]);
  console.log("click");
});

window.addEventListener("scroll", () => {
  const header = document.querySelector("header");

  header.classList.toggle("sticky", window.scrollY > 0);
});
