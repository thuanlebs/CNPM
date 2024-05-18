const $ = document.querySelector.bind(document);
const $$ = document.querySelectorAll.bind(document);

/**
 * jsFilter
 */
document.addEventListener("DOMContentLoaded", function () {
  $(".jsFilter").addEventListener("click", function () {
    $(".filter-menu").classList.toggle("active");
  });

  $(".grid").addEventListener("click", function () {
    $(".list").classList.remove("active");
    $(".grid").classList.add("active");
    $(".products-area-wrapper").classList.add("gridView");
    $(".products-area-wrapper").classList.remove("tableView");
  });

  $(".list").addEventListener("click", function () {
    $(".list").classList.add("active");
    $(".grid").classList.remove("active");
    $(".products-area-wrapper").classList.remove("gridView");
    $(".products-area-wrapper").classList.add("tableView");
  });
});
